from typing import List, Optional

from ninja import ModelSchema

from ..models import Match, MatchPlayer, MatchTeam


class MatchPlayerSchema(ModelSchema):
    match_id: int
    team_id: int
    user_id: int

    class Config:
        model = MatchPlayer
        model_exclude = ['user', 'team']

    @staticmethod
    def resolve_user_id(obj):
        return obj.user.id

    @staticmethod
    def resolve_match_id(obj):
        return obj.team.match.id

    @staticmethod
    def resolve_team_id(obj):
        return obj.team.id


class MatchTeamSchema(ModelSchema):
    players: Optional[List[MatchPlayerSchema]] = None
    match_id: int

    class Config:
        model = MatchTeam
        model_exclude = ['match']

    @staticmethod
    def resolve_match_id(obj):
        return obj.match.id


class MatchSchema(ModelSchema):
    server_ip: str
    create_date: str
    teams: List[MatchTeamSchema]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    rounds: int
    winner_id: Optional[int] = None

    class Config:
        model = Match
        model_exclude = ['server']

    @staticmethod
    def resolve_server_ip(obj):
        return obj.server.ip

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

    @staticmethod
    def resolve_winner_id(obj):
        if obj.winner:
            return obj.winner.id
        return None
