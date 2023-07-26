from typing import Optional

import pydantic
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja import ModelSchema, Schema

from ..models import Account

User = get_user_model()


class AccountSchema(ModelSchema):
    steamid: Optional[str]
    username: Optional[str]
    avatar: Optional[dict]
    steam_url: Optional[str]

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
        return obj.avatar_dict

    @staticmethod
    def resolve_steam_url(obj):
        return obj.user.steam_user.profileurl


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
    def resolve_lobby_id(obj):
        if hasattr(obj, 'account'):
            if obj.account.lobby:
                return obj.account.lobby.id

        return None

    @staticmethod
    def resolve_match_id(obj):
        if hasattr(obj, 'account'):
            if obj.account.get_match():
                return obj.account.get_match().id

        return None

    @staticmethod
    def resolve_pre_match_id(obj):
        if hasattr(obj, 'account'):
            if obj.account.pre_match:
                return obj.account.pre_match.id

        return None


class FakeUserSchema(UserSchema):
    token: Optional[str] = None
    verification_token: str

    @staticmethod
    def resolve_token(obj):
        return obj.auth.get_token()

    @staticmethod
    def resolve_verification_token(obj):
        if hasattr(obj, 'account') and obj.account is not None:
            return obj.account.verification_token


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
