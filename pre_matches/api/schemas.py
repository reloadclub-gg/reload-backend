from ninja import Field, Schema


class PreMatchSchema(Schema):
    id: int
    status: str
    # TODO: Remove state alias after https://github.com/3C-gg/reload-frontend/issues/774 is done.
    state: str = Field(None, alias='status')
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
