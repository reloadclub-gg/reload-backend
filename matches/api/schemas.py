from typing import List, Optional

from django.contrib.auth import get_user_model
from ninja import Field, ModelSchema, Schema

from accounts.utils import calc_level_and_points, steamid64_to_hex
from steam import Steam

from .. import models

User = get_user_model()


class MatchPlayerStatsSchema(ModelSchema):
    rounds_played: int = None
    clutches: int = None
    shots_hit: int = None
    adr: float = None
    kdr: float = None
    kda: float = None
    ahk: float = None
    ahr: float = None
    accuracy: float = None
    head_accuracy: float = None
    chest_accuracy: float = None
    others_accuracy: float = None

    class Config:
        model = models.MatchPlayerStats
        model_exclude = ['player', 'id']


class MatchPlayerProgressSchema(ModelSchema):
    level_before: int = Field(None, alias='level')
    level_after: int = None
    level_points_before: int = Field(None, alias='level_points')
    level_points_after: int = None
    points_earned: int = None

    class Config:
        model = models.MatchPlayer
        model_exclude = ['id', 'user', 'team', 'level', 'level_points']

    @staticmethod
    def resolve_level_after(obj):
        if obj.points_earned:
            return calc_level_and_points(
                obj.points_earned, obj.level, obj.level_points
            )[0]

        return obj.level

    @staticmethod
    def resolve_level_points_after(obj):
        if obj.points_earned:
            return calc_level_and_points(
                obj.points_earned, obj.level, obj.level_points
            )[1]

        return obj.level_points


class MatchPlayerSchema(ModelSchema):
    match_id: int
    team_id: int
    user_id: int
    username: str
    avatar: dict
    stats: MatchPlayerStatsSchema
    progress: MatchPlayerProgressSchema
    level: int
    status: str

    class Config:
        model = models.MatchPlayer
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
        return obj.user.account.avatar_dict

    @staticmethod
    def resolve_progress(obj):
        return MatchPlayerProgressSchema.from_orm(obj)

    @staticmethod
    def resolve_level(obj):
        return obj.user.account.level

    @staticmethod
    def resolve_status(obj):
        return obj.user.status


class MatchTeamSchema(ModelSchema):
    players: Optional[List[MatchPlayerSchema]] = None
    match_id: int

    class Config:
        model = models.MatchTeam
        model_exclude = ['match']

    @staticmethod
    def resolve_match_id(obj):
        return obj.match.id


class MapSchema(ModelSchema):
    class Config:
        model = models.Map
        model_fields = '__all__'


class MatchSchema(ModelSchema):
    server_ip: str
    create_date: str
    teams: List[MatchTeamSchema]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    rounds: int
    winner_id: Optional[int] = None
    map: MapSchema

    class Config:
        model = models.Match
        model_exclude = ['server', 'chat']

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


class MatchUpdatePlayerStats(Schema):
    steamid: str
    kills: int
    headshot_kills: int
    deaths: int
    assists: int
    health: int
    damage: int
    shots_fired: int
    head_shots: int
    chest_shots: int
    other_shots: int
    kill_weapons: List[str] = []
    defuse: bool = False
    plant: bool = False
    firstkill: bool = False


class MatchUpdateSchema(Schema):
    team_a_score: int = 0
    team_b_score: int = 0
    end_reason: int = None
    players_stats: List[MatchUpdatePlayerStats] = []
    is_overtime: bool = False
    chat: list = None
    status: str = None


class MatchTeamPlayerFiveMSchema(ModelSchema):
    username: str
    steamid: str
    level: int
    avatar: str

    class Config:
        model = User
        model_fields = ['id']

    @staticmethod
    def resolve_steamid(obj):
        return steamid64_to_hex(obj.account.steamid)

    @staticmethod
    def resolve_level(obj):
        return obj.account.level

    @staticmethod
    def resolve_username(obj):
        return obj.account.username

    @staticmethod
    def resolve_avatar(obj):
        return Steam.build_avatar_url(obj.steam_user.avatarhash, 'medium')


class MatchFiveMSchema(ModelSchema):
    match_id: int = Field(None, alias='id')
    team_a_players: List[MatchTeamPlayerFiveMSchema]
    team_b_players: List[MatchTeamPlayerFiveMSchema]

    class Config:
        model = models.Match
        model_fields = ['map']

    @staticmethod
    def resolve_map_id(obj):
        return obj.map.id

    @staticmethod
    def resolve_team_a_players(obj):
        return [player.user for player in obj.team_a.players]

    @staticmethod
    def resolve_team_b_players(obj):
        return [player.user for player in obj.team_b.players]


class FiveMMatchResponseMock(Schema):
    status_code: int


class MatchListItemStatsSchema(Schema):
    adr: float = 0.00
    kdr: float = 0.00
    kda: str = '0/0/0'
    head_accuracy: int = 0
    firstkills: int = 0


class MatchListItemSchema(Schema):
    id: int
    map_name: str
    end_date: str
    won: bool
    score: str
    stats: MatchListItemStatsSchema
