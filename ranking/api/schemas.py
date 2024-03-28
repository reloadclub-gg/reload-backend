from ninja import Schema


class RankingItemSchema(Schema):
    user_id: int
    matches_played: int = 0
    matches_won: int = 0
    avatar: dict
    ranking_pos: int
    steam_url: str
    level: int
    level_points: int
    username: str
