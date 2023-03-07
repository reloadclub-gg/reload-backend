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

    class Config:
        model = Match
        model_fields = '__all__'

    @staticmethod
    def resolve_players(obj):
        return obj.matchplayer_set.all()
