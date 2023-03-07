from typing import List, Optional

from ninja import ModelSchema

from ..models import Match, MatchPlayer


class MatchPlayerSchema(ModelSchema):
    class Config:
        model = MatchPlayer
        model_exclude = [
            'match',
        ]


class MatchSchema(ModelSchema):
    players: Optional[List[MatchPlayerSchema]] = None
    rounds: int
    create_date: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    class Config:
        model = Match
        model_fields = '__all__'

    @staticmethod
    def resolve_players(obj):
        return obj.matchplayer_set.all()

    @staticmethod
    def resolve_create_date(obj):
        return obj.create_date.isoformat()

    @staticmethod
    def resolve_start_date(obj):
        if obj.start_date:
            return obj.start_date.isoformat()
        return None

    @staticmethod
    def resolve_end_date(obj):
        if obj.end_date:
            return obj.end_date.isoformat()
        return None
