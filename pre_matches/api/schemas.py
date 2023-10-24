from ninja import Schema


class PreMatchSchema(Schema):
    id: int
    status: str
    countdown: int = None
    players_ready_count: int
    players_total: int
    user_ready: bool = False

    @staticmethod
    def resolve_players_total(obj):
        return len(obj.players)

    @staticmethod
    def resolve_players_ready_count(obj):
        return len(obj.players_ready)
