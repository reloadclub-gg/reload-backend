from typing import List, Optional

from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema

from accounts.models import Account
from matches.api.schemas import MatchSchema
from matchmaking.api.schemas import LobbySchema
from steam import Steam

User = get_user_model()


class FriendSchema(ModelSchema):
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
            'report_points',
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


class FriendListSchema(Schema):
    online: List[FriendSchema]
    offline: List[FriendSchema]
