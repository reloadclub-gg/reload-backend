from __future__ import annotations

from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static
from django.utils.translation import gettext as _

from core.redis import RedisClient
from core.utils import generate_random_string
from lobbies.models import Lobby, LobbyInvite
from matches.models import Match, MatchPlayer
from notifications.models import Notification
from pre_matches.models import PreMatch
from steam import Steam

from ..utils import calc_level_and_points, create_social_auth

User = get_user_model()
cache = RedisClient()


def get_default_social_handles():
    return dict.fromkeys(Account.AVAILABLE_SOCIAL_HANDLES, None)


class Account(models.Model):
    VERIFICATION_TOKEN_LENGTH = 6
    DEBUG_VERIFICATION_TOKEN = "debug0"
    AVAILABLE_SOCIAL_HANDLES = ['twitch', 'youtube', 'discord']

    class MatchResults:
        WIN = 'V'
        DEFEAT = 'D'
        NOT_AVAILABLE = 'N/A'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    steamid = models.CharField(max_length=128)
    username = models.CharField(max_length=64)
    level = models.IntegerField(default=0)
    level_points = models.IntegerField(default=0)
    highest_level = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(
        validators=[MinLengthValidator(VERIFICATION_TOKEN_LENGTH)],
        max_length=VERIFICATION_TOKEN_LENGTH,
    )
    social_handles = models.JSONField(default=get_default_social_handles)

    class Meta:
        indexes = [
            models.Index(fields=['is_verified']),
            models.Index(fields=['steamid']),
        ]

    def get_avatar_url(self, size: str = 'small'):
        return Steam.build_avatar_url(
            self.user.steam_user.avatarhash,
            None if size == 'small' else size,
        )

    @property
    def avatar_dict(self):
        return {
            'small': self.get_avatar_url('small'),
            'medium': self.get_avatar_url('medium'),
            'large': self.get_avatar_url('full'),
        }

    @property
    def lobby(self) -> Lobby:
        return Lobby.get_current(self.user.id)

    @property
    def lobby_invites(self) -> List[LobbyInvite]:
        return LobbyInvite.get_by_to_user_id(self.user.id)

    @property
    def lobby_invites_sent(self) -> List[LobbyInvite]:
        return LobbyInvite.get_by_from_user_id(self.user.id)

    @property
    def pre_match(self) -> PreMatch:
        return PreMatch.get_by_player_id(self.user.id)

    @property
    def second_chance_lvl(self) -> bool:
        return cache.sismember('__accounts:second_chance_lvl_users', self.user.id)

    @property
    def notifications(self) -> List[Notification]:
        return Notification.get_all_by_user_id(self.user.id)

    @property
    def matches_won(self) -> int:
        """
        Get how many matches a user played and won.
        """
        # Fetch all played matches
        played_matches = self.get_matches_played()

        # Count victories
        victories = sum(
            1
            for match in played_matches
            if match.winner and match.winner.has_player(self.user)
        )

        return victories

    @property
    def highest_win_streak(self) -> int:
        """
        Get the highest win streak for a user.
        """

        # Get all matches played by the user in ascending order
        played_matches = self.get_matches_played(asc=True)

        # Initialize counters
        max_streak = 0
        current_streak = 0

        # Go through all matches
        for match in played_matches:
            # If user's team won the match, increment the streak counter
            if match.winner and match.winner.has_player(self.user):
                current_streak += 1
                # Update maximum streak if current streak is larger
                max_streak = max(max_streak, current_streak)
            else:
                # Reset current streak if the match was not won by the user's team
                current_streak = 0

        return max_streak

    def __str__(self):
        return self.user.email

    def generate_verification_token(self):
        if settings.ENVIRONMENT == settings.LOCAL:
            return self.DEBUG_VERIFICATION_TOKEN

        length = self.VERIFICATION_TOKEN_LENGTH
        return generate_random_string(
            length=length,
            allowed_chars='digits',
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            if not self.user.steam_user:
                raise ValidationError(_('Steam account not found.'))

            self.verification_token = self.generate_verification_token()
            self.steamid = self.user.steam_user.steamid
            self.username = self.user.steam_user.username

        super(Account, self).save(*args, **kwargs)

    def notify(self, content: str, from_user_id: int = None):
        avatar = Account.get_notification_avatar_url(from_user_id)
        return Notification.create(
            content,
            avatar,
            from_user_id=from_user_id,
            to_user_id=self.user.id,
        )

    def get_match(self) -> Match:
        exclude_statuses = [Match.Status.FINISHED, Match.Status.CANCELLED]
        active_matches = MatchPlayer.objects.filter(user=self.user).exclude(
            team__match__status__in=exclude_statuses
        )

        if active_matches.count() > 1:
            # TODO send alert to admin
            raise ValidationError(_('User should not be in more than one match.'))

        match_player = active_matches.first()
        if match_player is not None:
            return match_player.team.match

        return None

    def set_second_chance_lvl(self):
        """
        Add user_id in a Redis set of users that
        can get to 0 points and play another match
        """
        cache.sadd('__accounts:second_chance_lvl_users', self.user.id)

    def remove_second_chance_lvl(self):
        """
        Remove user_id in a Redis set of users that
        can get to 0 points and play another match
        """
        cache.srem('__accounts:second_chance_lvl_users', self.user.id)

    def get_latest_matches_results(self, amount: int = 5) -> List[str]:
        """
        Returns a list with the last `amount` results.
        List item can be "V" for victory, "D" for defeat or "N/A" for not available.
        """
        matches = self.get_matches_played().order_by('-end_date')[:amount]
        played_results = [
            Account.MatchResults.WIN
            if match.get_user_team(self.user.id).id == match.winner.id
            else Account.MatchResults.DEFEAT
            for match in matches
        ]

        not_available_count = max(0, amount - len(played_results))
        return (
            played_results + [Account.MatchResults.NOT_AVAILABLE] * not_available_count
        )

    def get_most_stat_in_match(self, stat_name: str) -> int:
        matches_player = self.user.matchplayer_set.filter(
            team__match__status=Match.Status.FINISHED
        )
        max_stat = matches_player.aggregate(models.Max('stats__{}'.format(stat_name)))[
            'stats__{}__max'.format(stat_name)
        ]

        return max_stat

    def apply_points_earned(self, points_earned: int):
        level, level_points = calc_level_and_points(
            points_earned,
            self.level,
            self.level_points,
        )

        if self.level != level or self.level_points != level_points:
            if self.level != level:
                self.level = level
                # Sets user highest_level if the new level is the highest
                if level > self.highest_level:
                    self.highest_level = level
            self.level_points = level_points
            self.save()

    def check_friendship(self, friend_account: Account) -> bool:
        steam_friends = Steam.get_player_friends(self.user.steam_user)
        steam_friends_ids = [friend.get('steamid') for friend in steam_friends]
        return friend_account.steamid in steam_friends_ids

    def get_matches_played(self, asc=False) -> List[Match]:
        return Match.objects.filter(
            matchteam__matchplayer__user=self.user,
            status=Match.Status.FINISHED,
        ).order_by('-end_date' if not asc else 'end_date')

    def get_matches_played_count(self, asc=False) -> List[Match]:
        return Match.objects.filter(
            matchteam__matchplayer__user=self.user,
            status=Match.Status.FINISHED,
        ).count()

    def fetch_steam_friends(self) -> list:
        steam_friends = Steam.get_player_friends(self.user.steam_user)
        steam_friends_ids = {
            friend['steamid']
            for friend in steam_friends
            if friend['steamid'] != self.user.steam_user.steamid
        }

        # it will perform better by getting all accounts and then
        # filter the steamids in python
        all_accounts = Account.objects.filter(
            user__is_active=True,
            is_verified=True,
            user__is_staff=False,
        ).prefetch_related('user')

        friends_accounts = [
            account for account in all_accounts if account.steamid in steam_friends_ids
        ]

        if friends_accounts:
            cache.sadd(
                f'__friendlist:user:{self.user.id}',
                *[friend_account.user.id for friend_account in friends_accounts],
            )

        return friends_accounts

    def get_friends(self) -> list:
        if settings.TEST_MODE:
            Account.objects.filter(
                user__is_active=True,
                is_verified=True,
                user__is_staff=False,
            ).exclude(user_id=self.user.id)
        else:
            friends_ids = cache.smembers(f'__friendlist:user:{self.user.id}')
            if not friends_ids:
                return self.fetch_steam_friends()

            return Account.objects.filter(user__id__in=friends_ids)

    def get_online_friends(self) -> list:
        return [friend for friend in self.get_friends() if friend.user.is_online]

    @staticmethod
    def get_notification_avatar_url(user_id: int = None):
        if user_id is None:
            return static('brand/logo_icon.png')

        from_user = User.objects.get(pk=user_id)
        return Steam.build_avatar_url(from_user.steam_user.avatarhash, 'medium')


class Invite(models.Model):
    MAX_INVITES_PER_ACCOUNT = 4

    owned_by = models.ForeignKey(Account, on_delete=models.CASCADE)
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_updated = models.DateTimeField(auto_now=True, editable=False)
    email = models.EmailField()
    datetime_accepted = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        unique_together = ['owned_by', 'email']

    def clean(self):
        if not self.owned_by.user.is_staff:
            if len(self.owned_by.invite_set.all()) >= self.MAX_INVITES_PER_ACCOUNT:
                raise ValidationError(
                    _(f'Maximum invites reached ({self.MAX_INVITES_PER_ACCOUNT}).')
                )

        if self.datetime_accepted:
            raise ValidationError(_('Accepted invites cannot be modified.'))

        if User.objects.filter(email=self.email).exists():
            raise ValidationError(_('An invite already exists for this email.'))

    def __str__(self):
        return self.email


@receiver(post_save, sender=User)
def create_steam_and_account(sender, instance, created, **kwargs):
    if created:
        if instance.is_staff or instance.is_superuser:
            create_social_auth(instance, username=instance.email)
            Account.objects.create(user=instance)
