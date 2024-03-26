from ninja import ModelSchema

from accounts.models import Account


class RankingItemSchema(ModelSchema):
    user_id: int
    matches_played: int = 0
    matches_won: int = 0
    avatar: dict = {}
    ranking_pos: int = None

    class Config:
        model = Account
        model_fields = ["level", "level_points", "username"]

    @staticmethod
    def resolve_user_id(obj):
        return obj.user.id

    @staticmethod
    def resolve_matches_played(obj):
        return obj.get_matches_played_count()

    @staticmethod
    def resolve_matches_won(obj):
        return obj.matches_won

    @staticmethod
    def resolve_avatar(obj):
        return obj.avatar_dict
