from __future__ import annotations

from functools import cached_property
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext as _

from appsettings.services import player_max_level, player_max_level_points
from core.redis import RedisClient
from core.utils import generate_random_string
from matches.models import Match, MatchPlayer
from matchmaking.models import Lobby, LobbyInvite, PreMatch
from steam import Steam

User = get_user_model()
cache = RedisClient()


class Account(models.Model):
    VERIFICATION_TOKEN_LENGTH = 6
    DEBUG_VERIFICATION_TOKEN = "debug0"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    steamid = models.CharField(max_length=128)
    level = models.IntegerField(default=0)
    level_points = models.IntegerField(default=0)
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

    @cached_property
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
        qs = MatchPlayer.objects.filter(user=self.user).exclude(
            team__match__status=Match.Status.FINISHED
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

    def set_level_points(self, level_points):
        """
        This method is meant for give/take level_points to/from a particular user account.
        Some rules should be followed:
        - player should get to next level upon reach max points of current level
            - the remaning points should be increased on the next level
        - if player is on max level, it should not get to next level, thus it doesn't exist
        - if player is on min level (0), it should not get to prev level, thus it doesn't exist
        - if player reaches 0 points of a level, it should get another chance
        to stay on that level before get to a prev level
        - if a player reaches 0 points or less  2 times in a row, then it should get
        to prev level if applicable
        """
        max_points = player_max_level_points()
        max_lvl = player_max_level()

        if level_points > max_points or level_points < (max_points * -1):
            raise ValidationError(
                _('Level points should never exceed max level points.')
            )

        if level_points + self.level_points >= max_points:
            # Player get to next level upon max points reached
            if self.level == max_lvl:
                # If player is on max level, it should not get to next level,
                # thus it doesn't exist
                self.level_points += level_points
                self.save()
            else:
                # The remaning points should be increased on the next level
                self.level += 1
                self.level_points = (
                    level_points + self.level_points - settings.PLAYER_MAX_LEVEL_POINTS
                )
                self.set_second_chance_lvl()
                self.save()
        elif level_points + self.level_points <= 0:
            # Player get to prev level upon min points reached - if applicable
            if self.level == 0:
                # If player is on min level (0), it should not get to prev level,
                # thus it doesn't exist
                self.level_points = 0
                self.save()
            else:
                if self.second_chance_lvl:
                    # If player reaches 0 points of a level,
                    # it should get another chance to stay on that level
                    # before get to a prev level
                    self.remove_second_chance_lvl()
                    self.level_points = 0
                    self.save()
                else:
                    # If a player reaches 0 points or less 2 times in a row,
                    # then it should get to prev level
                    self.level -= 1
                    self.level_points = max_points + (level_points + self.level_points)
                    self.set_second_chance_lvl()
                    self.save()
        else:
            # If there isn't any change on levels, just in points,
            # we just incr the points
            self.level_points += level_points
            self.set_second_chance_lvl()
            self.save()


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
