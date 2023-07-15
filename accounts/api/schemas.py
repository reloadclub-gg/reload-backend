from typing import List, Optional

import pydantic
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja import ModelSchema, Schema

from lobbies.api.schemas import LobbySchema
from matches.api.schemas import MatchSchema
from steam import Steam

from ..models import Account

User = get_user_model()


class FriendAccountSchema(ModelSchema):
    id: Optional[int]
    steamid: Optional[str]
    username: Optional[str]
    avatar: Optional[dict]
    is_online: Optional[bool]
    status: Optional[str]
    lobby: Optional[LobbySchema]
    steam_url: Optional[str]
    match: Optional[MatchSchema] = None
    matches_played: int
    latest_matches_results: List[str]

    class Config:
        model = Account
        model_exclude = [
            'id',
            'user',
            'verification_token',
            'is_verified',
            'highest_level',
        ]

    @staticmethod
    def resolve_id(obj):
        return obj.user.id

    @staticmethod
    def resolve_is_online(obj):
        return bool(obj.user.auth.sessions)

    @staticmethod
    def resolve_steamid(obj):
        return obj.user.steam_user.steamid

    @staticmethod
    def resolve_username(obj):
        return obj.user.steam_user.username

    @staticmethod
    def resolve_avatar(obj):
        return {
            'small': Steam.build_avatar_url(obj.user.steam_user.avatarhash),
            'medium': Steam.build_avatar_url(obj.user.steam_user.avatarhash, 'medium'),
            'large': Steam.build_avatar_url(obj.user.steam_user.avatarhash, 'full'),
        }

    @staticmethod
    def resolve_status(obj):
        return obj.user.status

    @staticmethod
    def resolve_steam_url(obj):
        return obj.user.steam_user.profileurl

    @staticmethod
    def resolve_matches_played(obj):
        return len(obj.matches_played)

    @staticmethod
    def resolve_latest_matches_results(obj):
        return obj.get_latest_matches_results()


class AccountSchema(ModelSchema):
    steamid: Optional[str]
    username: Optional[str]
    avatar: Optional[dict]
    steam_url: Optional[str]
    matches_played: int
    latest_matches_results: List[str]

    class Config:
        model = Account
        model_exclude = [
            'id',
            'user',
            'verification_token',
            'highest_level',
        ]

    @staticmethod
    def resolve_avatar(obj):
        return {
            'small': Steam.build_avatar_url(obj.user.steam_user.avatarhash),
            'medium': Steam.build_avatar_url(obj.user.steam_user.avatarhash, 'medium'),
            'large': Steam.build_avatar_url(obj.user.steam_user.avatarhash, 'full'),
        }

    @staticmethod
    def resolve_steam_url(obj):
        return obj.user.steam_user.profileurl

    @staticmethod
    def resolve_matches_played(obj):
        return len(obj.matches_played)

    @staticmethod
    def resolve_latest_matches_results(obj):
        return obj.get_latest_matches_results()


class UserSchema(ModelSchema):
    account: Optional[AccountSchema] = None
    email: Optional[pydantic.EmailStr] = None
    is_online: bool = None
    status: str
    lobby_id: int = None
    match_id: int = None
    pre_match_id: str = None

    class Config:
        model = User
        model_exclude = [
            'is_staff',
            'groups',
            'user_permissions',
            'is_superuser',
            'password',
            'last_login',
            'date_joined',
            'date_inactivation',
            'date_email_update',
        ]

    @staticmethod
    def resolve_account(obj):
        if hasattr(obj, 'account'):
            return obj.account

        return None

    @staticmethod
    def resolve_email(obj):
        if hasattr(obj, 'email'):
            return obj.email

        return ''

    @staticmethod
    def resolve_lobby_id(obj):
        if hasattr(obj, 'account'):
            if obj.account.lobby:
                return obj.account.lobby.id

        return None

    @staticmethod
    def resolve_match_id(obj):
        if hasattr(obj, 'account'):
            if obj.account.match:
                return obj.account.match.id

        return None

    @staticmethod
    def resolve_pre_match_id(obj):
        if hasattr(obj, 'account'):
            if obj.account.pre_match:
                return obj.account.pre_match.id

        return None


class FakeUserSchema(UserSchema):
    token: Optional[str] = None

    @staticmethod
    def resolve_token(obj):
        return obj.auth.get_token()


class SignUpSchema(Schema):
    email: pydantic.EmailStr
    terms: bool
    policy: bool

    @pydantic.validator('email')
    def email_must_be_unique(cls, v):
        assert not User.objects.filter(email=v).exists(), _('E-mail must be unique.')
        return v

    @pydantic.validator('terms')
    def terms_must_be_true(cls, v):
        assert v, _('User must read and agree with our Terms and Policy.')
        return v

    @pydantic.validator('policy')
    def policy_must_be_true(cls, v):
        assert v, _('User must read and agree with our Terms and Policy.')
        return v


class FakeSignUpSchema(Schema):
    email: pydantic.EmailStr


class VerifyUserEmailSchema(Schema):
    verification_token: str


class UserUpdateSchema(Schema):
    email: pydantic.EmailStr = None
    verification_token: str = None

    @pydantic.root_validator
    def any_of(cls, v):
        assert any(v.values()), _(
            'One of e-mail or verification_token must have a value.'
        )
        return v

    @pydantic.validator('verification_token')
    def must_be_valid(cls, v):
        if v:
            assert Account.objects.filter(verification_token=v).exists(), _(
                'Invalid verification token.'
            )
        return v


class UpdateUserEmailSchema(Schema):
    email: pydantic.EmailStr

    @pydantic.validator('email')
    def email_must_be_unique(cls, v):
        assert not User.objects.filter(email=v).exists(), _('E-mail must be unique.')
        return v
