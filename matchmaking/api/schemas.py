from typing import List, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone
from ninja import Schema

from steam import Steam

from ..models import Lobby, LobbyInvite, PreMatch, PreMatchConfig

User = get_user_model()


class LobbyPlayerSchema(Schema):
    id: Optional[int]
    steamid: Optional[str]
    username: Optional[str]
    avatar: Optional[dict]
    is_online: Optional[bool]
    level: Optional[int]
    status: Optional[str]
    steam_url: Optional[str]

    class Config:
        model = User

    @staticmethod
    def resolve_steamid(obj):
        return obj.steam_user.steamid

    @staticmethod
    def resolve_username(obj):
        return obj.steam_user.username

    @staticmethod
    def resolve_avatar(obj):
        return {
            'small': Steam.build_avatar_url(obj.steam_user.avatarhash),
            'medium': Steam.build_avatar_url(obj.steam_user.avatarhash, 'medium'),
            'large': Steam.build_avatar_url(obj.steam_user.avatarhash, 'full'),
        }

    @staticmethod
    def resolve_level(obj):
        return obj.account.level

    @staticmethod
    def resolve_steam_url(obj):
        return obj.steam_user.profileurl


class LobbySchema(Schema):
    id: int
    owner_id: int
    lobby_type: str
    mode: int
    max_players: int
    players_ids: list
    players: List[LobbyPlayerSchema]
    players_count: int
    non_owners_ids: list
    is_public: bool
    invites: List[LobbyInvite]
    invited_players_ids: list
    overall: int
    seats: int
    queue: Optional[str]
    queue_time: Optional[int]
    restriction_countdown: Optional[int]

    class Config:
        model = Lobby

    @staticmethod
    def resolve_queue(obj):
        return obj.queue.strftime('%Y-%m-%d %H:%M:%S') if obj.queue else None

    @staticmethod
    def resolve_players(obj):
        return [User.objects.get(pk=user_id) for user_id in obj.players_ids]


class LobbyInviteSchema(Schema):
    id: str
    lobby_id: int
    lobby: LobbySchema
    from_player: LobbyPlayerSchema
    to_player: LobbyPlayerSchema
    create_date: timezone.datetime

    class Config:
        model = LobbyInvite

    @staticmethod
    def resolve_from_player(obj):
        return User.objects.get(pk=obj.from_id)

    @staticmethod
    def resolve_to_player(obj):
        return User.objects.get(pk=obj.to_id)

    @staticmethod
    def resolve_lobby(obj):
        return Lobby(owner_id=obj.lobby_id)


class PreMatchSchema(Schema):
    id: str
    state: str
    countdown: Optional[int]
    players_ready_count: int
    players_total: int
    user_ready: Optional[bool] = False

    class Config:
        model = PreMatch

    @staticmethod
    def resolve_state(obj):
        return list(PreMatchConfig.STATES.keys())[
            list(PreMatchConfig.STATES.values()).index(obj.state)
        ]

    @staticmethod
    def resolve_players_total(obj):
        return len(obj.players)

    @staticmethod
    def resolve_players_ready_count(obj):
        return len(obj.players_ready)
