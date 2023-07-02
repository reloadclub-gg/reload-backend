from ninja import Schema

from ..models import PreMatch


class PreMatchSchema(Schema):
    id: str
    state: str
    countdown: int = None
    players_ready_count: int
    players_total: int
    user_ready: bool = False

    @staticmethod
    def resolve_state(obj):
        return list(PreMatch.Config.STATES.keys())[
            list(PreMatch.Config.STATES.values()).index(obj.state)
        ]

    @staticmethod
    def resolve_players_total(obj):
        return len(obj.players)

    @staticmethod
    def resolve_players_ready_count(obj):
        return len(obj.players_ready)
