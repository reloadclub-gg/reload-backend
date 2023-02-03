from functools import cached_property
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils.translation import gettext as _

from core.utils import generate_random_string
from matchmaking.models import Lobby, LobbyInvite
from steam import Steam

User = get_user_model()


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
