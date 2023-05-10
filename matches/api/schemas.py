from typing import List, Optional

from ninja import Field, ModelSchema

from accounts.utils import calc_level_and_points
from steam import Steam

from ..models import Match, MatchPlayer, MatchPlayerStats, MatchTeam


class MatchPlayerStatsSchema(ModelSchema):
    class Config:
        model = MatchPlayerStats
        model_exclude = ['player', 'id']


class MatchPlayerProgressSchema(ModelSchema):
    level_before: int = Field(None, alias='level')
    level_after: int = None
    level_points_before: int = Field(None, alias='level_points')
    level_points_after: int = None
    points_earned: int = None

    class Config:
        model = MatchPlayer
        model_exclude = ['id', 'user', 'team', 'level', 'level_points']

    @staticmethod
    def resolve_level_after(obj):
        if obj.points_earned:
            return calc_level_and_points(
                obj.points_earned, obj.level, obj.level_points
            )[0]

    @staticmethod
    def resolve_level_points_after(obj):
        if obj.points_earned:
            return calc_level_and_points(
                obj.points_earned, obj.level, obj.level_points
            )[1]


class MatchPlayerSchema(ModelSchema):
    match_id: int
    team_id: int
    user_id: int
    username: str
    avatar: dict
    stats: MatchPlayerStatsSchema
    progress: MatchPlayerProgressSchema

    class Config:
        model = MatchPlayer
        model_exclude = ['user', 'team', 'level', 'level_points']

    @staticmethod
    def resolve_user_id(obj):
        return obj.user.id

    @staticmethod
    def resolve_match_id(obj):
        return obj.team.match.id

    @staticmethod
    def resolve_team_id(obj):
        return obj.team.id

    @staticmethod
    def resolve_username(obj):
        return obj.user.steam_user.username

    @staticmethod
    def resolve_avatar(obj):
        return {
            'small': Steam.build_avatar_url(obj.user.steam_user.avatarhash),
            'medium': Steam.build_avatar_url(obj.user.steam_user.avatarhash, 'medium'),
            'large': Steam.build_avatar_url(obj.user.steam_user.avatarhash, 'full'),
        }

    @staticmethod
    def resolve_progress(obj):
        return MatchPlayerProgressSchema.from_orm(obj)


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
    status: str

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

    @staticmethod
    def resolve_status(obj):
        if obj.status == Match.Status.LOADING:
            return 'loading'
        elif obj.status == Match.Status.RUNNING:
            return 'running'
        else:
            return 'finished'
