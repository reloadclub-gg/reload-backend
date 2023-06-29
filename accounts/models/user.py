from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from pydantic import BaseModel, Field
from social_django.models import UserSocialAuth

from .auth import Auth


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email, and password.
        """
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

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class SteamUser(BaseModel):
    steamid: str = None
    username: str = Field(None, alias='personaname')
    avatarhash: str = None
    communityvisibilitystate: int = None
    profileurl: str = None


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField('staff status', default=False)
    is_active = models.BooleanField('active', default=True)
    date_joined = models.DateTimeField('date joined', default=timezone.now)
    date_inactivation = models.DateTimeField('date inactivation', blank=True, null=True)
    date_email_update = models.DateTimeField(
        'latest email update date', blank=True, null=True
    )

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def inactivate(self):
        self.is_active = False
        self.date_inactivation = timezone.now()
        self.save()

    @property
    def steam_user(self):
        social_user = UserSocialAuth.objects.filter(user=self).first()
        if not social_user:
            return None

        return SteamUser(**social_user.extra_data.get('player'))

    @property
    def auth(self):
        return Auth(user_id=self.id)

    @property
    def is_online(self):
        return self.auth.sessions is not None

    @property
    def status(self):
        if hasattr(self, 'account') and self.account.is_verified:
            if self.account.match:
                return 'in_game'

            pre_match = self.account.pre_match
            if pre_match and pre_match.state >= 0:
                return 'queued'

            lobby = self.account.lobby
            if lobby:
                if lobby.queue:
                    return 'queued'

                if lobby.players_count > 1:
                    return 'teaming'

            if self.is_online:
                return 'online'

        return 'offline'

    @staticmethod
    def online_users():
        active_users = User.objects.filter(
            is_active=True, is_superuser=False, is_staff=False
        )
        online_users_ids = [user.id for user in active_users if user.is_online]
        return active_users.filter(id__in=online_users_ids)

    def __str__(self):
        return self.email if self.email else str(self.id)


class UserLogin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=128, blank=True, null=True, editable=False)

    class Meta:
        unique_together = ['user', 'ip_address']
        get_latest_by = 'timestamp'

    def __str__(self):
        return f"{self.user.email} - {self.timestamp}"
