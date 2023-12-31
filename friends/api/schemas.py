from typing import List

from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema

from accounts.models import Account

from .. import models

User = get_user_model()


class FriendSchema(ModelSchema):
    user_id: int
    steamid: str
    username: str
    avatar: dict
    status: str
    steam_url: str
    lobby_id: int = None

    class Config:
        model = Account
        model_exclude = [
            'id',
            'user',
            'verification_token',
            'is_verified',
            'highest_level',
            'social_handles',
            'coins',
        ]

    @staticmethod
    def resolve_user_id(obj):
        return obj.user.id

    @staticmethod
    def resolve_avatar(obj):
        return obj.avatar_dict

    @staticmethod
    def resolve_status(obj):
        return obj.user.status

    @staticmethod
    def resolve_steam_url(obj):
        return obj.user.steam_user.profileurl

    @staticmethod
    def resolve_lobby_id(obj):
        if obj.lobby:
            return obj.lobby.id
        return None


class FriendshipSchema(ModelSchema):
    user_from: FriendSchema
    user_to: FriendSchema
    create_date: str

    class Config:
        model = models.Friendship
        model_exclude = ['create_date']

    @staticmethod
    def resolve_user_from(obj):
        return obj.user_from.account

    @staticmethod
    def resolve_user_to(obj):
        return obj.user_to.account

    @staticmethod
    def resolve_create_date(obj):
        return obj.create_date.isoformat()


class FriendListSchema(Schema):
    requests: dict
    online: List[FriendSchema]
    offline: List[FriendSchema]
