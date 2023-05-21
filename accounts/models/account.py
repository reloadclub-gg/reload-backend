from __future__ import annotations

from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext as _

from core.redis import RedisClient
from core.utils import generate_random_string
from matches.models import Match, MatchPlayer
from matchmaking.models import Lobby, LobbyInvite, PreMatch
from notifications.models import Notification
from steam import Steam

from ..utils import calc_level_and_points

User = get_user_model()
cache = RedisClient()


class Account(models.Model):
    VERIFICATION_TOKEN_LENGTH = 6
    DEBUG_VERIFICATION_TOKEN = "debug0"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    steamid = models.CharField(max_length=128)
    level = models.IntegerField(default=0)
    level_points = models.IntegerField(default=0)
    highest_level = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(
        validators=[MinLengthValidator(VERIFICATION_TOKEN_LENGTH)],
        max_length=VERIFICATION_TOKEN_LENGTH,
    )
    report_points = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self._state.adding:
            if not self.user.steam_user:
                raise ValidationError(_('Steam account not found.'))

            if settings.ENVIRONMENT == settings.LOCAL:
                self.verification_token = self.DEBUG_VERIFICATION_TOKEN
            else:
                length = self.VERIFICATION_TOKEN_LENGTH
                self.verification_token = generate_random_string(
                    length=length, allowed_chars='digits'
                )

            self.steamid = self.user.steam_user.steamid

        super(Account, self).save(*args, **kwargs)

    def __str__(self):
        return self.user.email

    @property
    def steam_friends(self) -> list:
        return Steam.get_player_friends(self.user.steam_user)

    @property
    def friends(self) -> list:
        steam_friends_ids = [friend.get('steamid') for friend in self.steam_friends]

        return [
            account
            for account in Account.objects.filter(
                user__is_active=True,
                is_verified=True,
                user__is_staff=False,
                steamid__in=steam_friends_ids,
            ).exclude(user_id=self.user.id)
        ]

    @property
    def online_friends(self) -> list:
        return [friend for friend in self.friends if friend.user.is_online]

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
    def match(self) -> Match:
        exclude_statues = [Match.Status.FINISHED, Match.Status.CANCELLED]
        qs = MatchPlayer.objects.filter(user=self.user).exclude(
            team__match__status__in=exclude_statues
        )
        if len(qs) > 1:
            # TODO send alert to admin
            raise ValidationError(_('User should not be in more then one match.'))

        match_player = qs.first()
        if match_player:
            return match_player.team.match

        return None

    @property
    def second_chance_lvl(self) -> bool:
        return cache.sismember('__accounts:second_chance_lvl_users', self.user.id)

    @property
    def notifications(self) -> List[Notification]:
        return Notification.get_all_by_user_id(self.user.id)

    def notify(self, content, from_user_id=None):
        if from_user_id:
            from_user = User.objects.get(pk=from_user_id)
            avatar = Steam.build_avatar_url(from_user.steam_user.avatarhash, 'medium')
        else:
            avatar = static('brand/logo_icon.png')

        return Notification.create(
            content, avatar, from_user_id=from_user_id, to_user_id=self.user.id
        )

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
        teams = [
            match.get_user_team(self.user.id) for match in self.matches_played[:amount]
        ]
        played_results = [
            'V' if team.match.winner.id == team.id else 'D' for team in teams
        ]
        not_available = ['N/A'] * (amount - len(played_results))
        return played_results + not_available

    def get_most_stat_in_match(self, stat_name: str) -> int:
        matches_player = self.user.matchplayer_set.filter(
            team__match__status=Match.Status.FINISHED
        )
        if matches_player:
            return max(
                [
                    getattr(match_player.stats, stat_name)
                    for match_player in matches_player
                ]
            )

        return None

    def apply_points_earned(self, points_earned: int):
        level, level_points = calc_level_and_points(
            points_earned, self.level, self.level_points
        )

        if self.level != level:
            self.level = level
            # Sets user highest_level if the new level is the highest
            if level > self.highest_level:
                self.highest_level = level

        self.level_points = level_points
        self.save()

    def check_friendship(self, friend_account: Account) -> bool:
        steam_friends_ids = [friend.get('steamid') for friend in self.steam_friends]
        return friend_account.steamid in steam_friends_ids

    @property
    def matches_played(self) -> List[Match]:
        """
        Returns all the finished matches a user played.
        """
        matches_ids = self.user.matchplayer_set.filter(
            team__match__status=Match.Status.FINISHED
        ).values_list('team__match__id', flat=True)

        return Match.objects.filter(id__in=matches_ids).order_by('-end_date')

    @property
    def match_wins(self) -> int:
        """
        Get how many matches a user played and won.
        """
        return len(
            [
                match
                for match in self.matches_played
                if match.get_user_team(self.user.id).id == match.winner.id
            ]
        )

    @property
    def highest_win_streak(self) -> int:
        teams = [match.get_user_team(self.user.id) for match in self.matches_played]
        results = [team.match.winner.id == team.id for team in teams]

        counter = 0
        max = 0
        for result in results:
            if result:
                counter += 1
                if counter > max:
                    max += 1
            else:
                counter = 0

        return max


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
