from typing import Optional

from django.contrib.auth import get_user_model
from ninja import Schema

from ..models import PreMatch, PreMatchConfig

User = get_user_model()


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
