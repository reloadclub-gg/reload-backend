from typing import List, Optional
from ninja import ModelSchema, Schema
from ..models import Lobby


class LobbySchema(Schema):
    id: Optional[int]
    owner_id: Optional[int]
    players_ids: Optional[list]

    class Config:
        model = Lobby

    @staticmethod
    def resolve_id(obj):
        return obj.id

    @staticmethod
    def resolve_owner_id(obj):
        return obj.owner_id

    @staticmethod
    def resolve_players_ids(obj):
        return sorted(obj.players_ids)
