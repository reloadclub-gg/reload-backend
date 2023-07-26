from typing import List, Optional

from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema
from pydantic import root_validator

from accounts.models import Account

from ..models import Lobby, LobbyInvite

User = get_user_model()


class LobbyPlayerSchema(ModelSchema):
    user_id: int
    avatar: dict
    matches_played: int
    latest_matches_results: list
    steam_url: str

    class Config:
        model = Account
        model_fields = ['level', 'username']

    @staticmethod
    def resolve_user_id(obj):
        return obj.user.id

    @staticmethod
    def resolve_avatar(obj):
        return obj.avatar_dict

    @staticmethod
    def resolve_matches_played(obj):
        return obj.get_matches_played_count()

    @staticmethod
    def resolve_latest_matches_results(obj):
        return obj.get_latest_matches_results()

    @staticmethod
    def resolve_steam_url(obj):
        return obj.user.steam_user.profileurl


class LobbySchema(Schema):
    id: int
    owner_id: int
    players_ids: list
    players: List[LobbyPlayerSchema]
    is_public: bool
    invites: List[LobbyInvite]
    invited_players_ids: list
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
        return Account.objects.filter(user__id__in=obj.players_ids)


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
