from datetime import datetime
from typing import Optional

from ninja import Schema

from ..models import Lobby


class LobbySchema(Schema):
    id: int
    owner_id: int
    lobby_type: str
    mode: int
    max_players: int
    players_ids: list
    is_public: bool
    invites: list
    invited_players_ids: list
    overall: int
    queue: Optional[datetime]
    queue_time: Optional[int]

    class Config:
        model = Lobby

    @staticmethod
    def resolve_id(obj):
        return obj.id

    @staticmethod
    def resolve_owner_id(obj):
        return obj.owner_id

    @staticmethod
    def resolve_lobby_type(obj):
        return obj.lobby_type

    @staticmethod
    def resolve_mode(obj):
        return obj.mode

    @staticmethod
    def resolve_max_players(obj):
        return obj.max_players

    @staticmethod
    def resolve_players_ids(obj):
        return sorted(obj.players_ids)

    @staticmethod
    def resolve_is_public(obj):
        return obj.is_public

    @staticmethod
    def resolve_invites(obj):
        return obj.invites

    @staticmethod
    def resolve_invited_players_ids(obj):
        return obj.invited_players_ids

    @staticmethod
    def resolve_overall(obj):
        return obj.overall

    @staticmethod
    def resolve_queue(obj):
        return obj.queue

    @staticmethod
    def resolve_queue_time(obj):
        return obj.queue_time
