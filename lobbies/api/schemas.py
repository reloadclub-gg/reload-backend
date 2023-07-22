from typing import List, Optional

from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema
from pydantic import Field, root_validator

from steam import Steam

from ..models import Lobby, LobbyInvite

User = get_user_model()


class LobbyPlayerSchema(ModelSchema):
    user_id: int = Field(alias='id')
    username: str
    steamid: str
    level: int
    level_points: int
    highest_level: int
    avatar: dict
    matches_played: int
    matches_won: int
    highest_win_streak: int
    latest_matches_results: list
    most_kills_in_a_match: int = None
    most_damage_in_a_match: int = None
    steam_url: str
    status: str
    lobby_id: int = None

    class Config:
        model = User
        model_exclude = [
            'email',
            'is_staff',
            'is_superuser',
            'date_joined',
            'date_inactivation',
            'date_email_update',
            'password',
            'last_login',
            'groups',
            'user_permissions',
            'id',
            'is_active',
        ]

    @staticmethod
    def resolve_username(obj):
        return obj.account.username

    @staticmethod
    def resolve_steamid(obj):
        return obj.account.steamid

    @staticmethod
    def resolve_level(obj):
        return obj.account.level

    @staticmethod
    def resolve_level_points(obj):
        return obj.account.level_points

    @staticmethod
    def resolve_highest_level(obj):
        return obj.account.highest_level

    @staticmethod
    def resolve_avatar(obj):
        return {
            'small': Steam.build_avatar_url(obj.steam_user.avatarhash),
            'medium': Steam.build_avatar_url(obj.steam_user.avatarhash, 'medium'),
            'large': Steam.build_avatar_url(obj.steam_user.avatarhash, 'full'),
        }

    @staticmethod
    def resolve_matches_played(obj):
        return len(obj.account.matches_played)

    @staticmethod
    def resolve_matches_won(obj):
        return obj.account.matches_won

    @staticmethod
    def resolve_highest_win_streak(obj):
        return obj.account.highest_win_streak

    @staticmethod
    def resolve_latest_matches_results(obj):
        return obj.account.get_latest_matches_results()

    @staticmethod
    def resolve_most_kills_in_a_match(obj):
        return obj.account.get_most_stat_in_match('kills')

    @staticmethod
    def resolve_most_damage_in_a_match(obj):
        return obj.account.get_most_stat_in_match('damage')

    @staticmethod
    def resolve_steam_url(obj):
        return obj.steam_user.profileurl

    @staticmethod
    def resolve_lobby_id(obj):
        return obj.account.lobby.id if obj.account.lobby else None


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
        return obj.queue.isoformat() if obj.queue else None

    @staticmethod
    def resolve_players(obj):
        return User.objects.filter(pk__in=obj.players_ids)


class LobbyInviteSchema(Schema):
    id: str
    lobby_id: int
    lobby: LobbySchema
    from_player: LobbyPlayerSchema
    to_player: LobbyPlayerSchema
    create_date: str

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

    @staticmethod
    def resolve_create_date(obj):
        return obj.create_date.isoformat()


class LobbyInviteDeleteSchema(Schema):
    accept: bool = False
    refuse: bool = False


class LobbyUpdateSchema(Schema):
    start_queue: bool = None
    cancel_queue: bool = None

    @root_validator
    def check_any(cls, values):
        assert any(values)
        return values


class LobbyInviteCreateSchema(Schema):
    lobby_id: int
    from_user_id: int
    to_user_id: int


class LobbyInviteWebsocketSchema(Schema):
    invite: LobbyInviteSchema
    status: str


class LobbyPlayerWebsocketUpdate(Schema):
    player: LobbyPlayerSchema
    lobby: LobbySchema
