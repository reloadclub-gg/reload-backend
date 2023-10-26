from __future__ import annotations

import json

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q
from django.utils import timezone
from pydantic import BaseModel, Field
from social_django.models import UserSocialAuth

from core.redis import redis_client_instance as cache

from .auth import Auth


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)


class SteamUser(BaseModel):
    user_id: int
    steamid: str = None
    username: str = Field(None, alias='personaname')
    avatarhash: str = None
    communityvisibilitystate: int = None
    profileurl: str = None

    class Config:
        CACHE_KEY = '__auth:steamuser'

    def save(self):
        payload = {k: v for k, v in self.dict().items() if v is not None}
        payload.update(personaname=self.username)
        del payload['username']
        return cache.hmset(
            f'{SteamUser.Config.CACHE_KEY}:{self.user_id}',
            payload,
        )

    @staticmethod
    def load(user_id: int):
        result = cache.hgetall(f'{SteamUser.Config.CACHE_KEY}:{user_id}')
        if result:
            return SteamUser(**result)


class User(AbstractBaseUser, PermissionsMixin):
    class Status(models.TextChoices):
        ONLINE = 'online'
        OFFLINE = 'offline'
        TEAMING = 'teaming'
        QUEUED = 'queued'
        IN_GAME = 'in_game'

    email = models.EmailField(unique=True)
    is_staff = models.BooleanField('staff status', default=False)
    is_active = models.BooleanField('active', default=True)
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    date_inactivation = models.DateTimeField('date inactivation', blank=True, null=True)
    date_email_update = models.DateTimeField(
        'latest email update date',
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default='offline',
    )

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_staff']),
            models.Index(fields=['status']),
        ]

    @property
    def steam_user(self):
        from_cache = SteamUser.load(self.id)
        if from_cache:
            return from_cache

        social_user = (
            UserSocialAuth.objects.select_related('user').filter(user=self).first()
        )
        if not social_user:
            return None

        if isinstance(social_user.extra_data, str):
            social_user.extra_data = json.loads(social_user.extra_data)

        payload = social_user.extra_data.get('player')
        payload.update(user_id=self.id)
        steamuser = SteamUser(**payload)
        steamuser.save()
        return steamuser

    @property
    def auth(self):
        return Auth(user_id=self.id)

    @property
    def is_online(self):
        return self.is_verified() and self.status != User.Status.OFFLINE

    @property
    def has_sessions(self):
        return self.auth.sessions is not None

    @property
    def is_in_game(self):
        return self.status == User.Status.IN_GAME

    @property
    def is_queued(self):
        return self.status == User.Status.QUEUED

    @property
    def is_teaming(self):
        return self.status == User.Status.TEAMING

    @property
    def is_available(self):
        return self.is_online and not self.is_in_game and not self.is_queued

    def __str__(self):
        return self.email if self.email else str(self.id)

    def has_account(self) -> bool:
        """
        Return weather the received user has an account.
        """
        return hasattr(self, 'account') and self.account is not None

    def is_verified(self) -> bool:
        """
        Return weather the received user has an account and is verified.
        """
        return self.is_active and self.has_account() and self.account.is_verified

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def inactivate(self):
        self.is_active = False
        self.date_inactivation = timezone.now()
        self.save()

    def add_session(self):
        sessions = self.auth.add_session()
        if sessions == 1:
            self.status = User.Status.ONLINE
            self.save()

    def remove_session(self):
        sessions = self.auth.remove_session()
        if sessions is None:
            self.status = User.Status.OFFLINE
            self.save()

    def logout(self):
        self.auth.expire_session(seconds=0)
        self.status = User.Status.OFFLINE
        self.save()

    @staticmethod
    def online_users():
        return User.objects.filter(~Q(status=User.Status.OFFLINE))


class UserLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=128, blank=True, null=True, editable=False)

    class Meta:
        unique_together = ['user', 'ip_address']
        get_latest_by = 'timestamp'

    def __str__(self):
        return f"{self.user.email} - {self.timestamp}"


class IdentityManager(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    agent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        editable=False,
        related_name='identities',
    )
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.agent.email} as {self.user.email} at {self.timestamp}"
