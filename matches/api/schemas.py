from typing import List, Optional

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja import Field, ModelSchema, Schema
from pydantic import root_validator, validator

from accounts.utils import calc_level_and_points, steamid64_to_hex
from core.utils import get_full_file_path
from steam import Steam
from store.models import Item

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
    hsk: int = None
    accuracy: int = None
    head_accuracy: int = None
    chest_accuracy: int = None
    others_accuracy: int = None

    class Config:
        model = models.MatchPlayerStats
        model_exclude = ["player", "id"]


class MatchPlayerProgressSchema(ModelSchema):
    level_before: int = Field(None, alias="level")
    level_after: int = None
    level_points_before: int = Field(None, alias="level_points")
    level_points_after: int = None
    points_earned: int = None

    class Config:
        model = models.MatchPlayer
        model_exclude = ["id", "user", "team", "level", "level_points"]

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
    steam_url: str

    class Config:
        model = models.MatchPlayer
        model_exclude = ["user", "team", "level", "level_points"]

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

    @staticmethod
    def resolve_lobby_id(obj):
        if obj.user.account.lobby:
            return obj.user.account.lobby.id

        return None

    @staticmethod
    def resolve_steam_url(obj):
        return obj.user.steam_user.profileurl


class MatchTeamSchema(ModelSchema):
    players: Optional[List[MatchPlayerSchema]] = None
    match_id: int

    class Config:
        model = models.MatchTeam
        model_exclude = ["match"]

    @staticmethod
    def resolve_match_id(obj):
        return obj.match.id


class MapSchema(ModelSchema):
    thumbnail: str = None

    class Config:
        model = models.Map
        model_fields = '__all__'
        model_exclude = ['weight']

    @staticmethod
    def resolve_thumbnail(obj):
        if obj.thumbnail:
            return get_full_file_path(obj.thumbnail)

        return None


class MatchSchema(ModelSchema):
    server_ip: str
    create_date: str
    teams: List[MatchTeamSchema]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    rounds: int
    winner_id: Optional[int] = None
    map: MapSchema
    match_type: str

    class Config:
        model = models.Match
        model_exclude = ["server", "chat"]

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


class MatchUpdateTeam(Schema):
    name: str
    players: List[MatchUpdatePlayerStats]
    score: int = 0


class MatchUpdateSchema(Schema):
    teams: List[MatchUpdateTeam] = []
    end_reason: int = None
    is_overtime: bool = False
    chat: list = None
    status: str = None


class MatchTeamPlayerFiveMSchema(ModelSchema):
    username: str
    steamid: str
    steamid64: str
    level: int
    avatar: str
    assets: dict = {}

    class Config:
        model = User
        model_fields = ['id']

    @staticmethod
    def resolve_steamid(obj):
        return steamid64_to_hex(obj.account.steamid)

    @staticmethod
    def resolve_steamid64(obj):
        return obj.account.steamid

    @staticmethod
    def resolve_level(obj):
        return obj.account.level

    @staticmethod
    def resolve_username(obj):
        return obj.account.username

    @staticmethod
    def resolve_avatar(obj):
        return Steam.build_avatar_url(obj.steam_user.avatarhash, 'medium')

    @staticmethod
    def resolve_assets(obj):
        item_types = {
            Item.ItemType.SPRAY: 'spray',
            Item.ItemType.PERSONA: 'persona',
            Item.ItemType.WEAR: 'wear',
            Item.ItemType.WEAPON: 'weapon',
        }

        items = obj.useritem_set.filter(
            item__item_type__in=item_types.keys(),
            in_use=True,
        )

        wear_items = []
        weapon_items = []
        item_mapping = {}
        for item in items:
            if item.item.item_type == Item.ItemType.WEAR:
                wear_items.append(item.item.handle)
            elif item.item.item_type == Item.ItemType.WEAPON:
                weapon_items.append(item.item.handle)
            else:
                item_mapping[item.item.item_type] = item

        item_mapping[Item.ItemType.WEAR] = wear_items if wear_items else None
        item_mapping[Item.ItemType.WEAPON] = weapon_items if weapon_items else None

        return {
            value: (
                item_mapping.get(key).item.handle
                if key in item_mapping
                and key not in [Item.ItemType.WEAR, Item.ItemType.WEAPON]
                else item_mapping.get(key)
            )
            for key, value in item_types.items()
        }


class MatchSpecFiveMSchema(ModelSchema):
    username: str
    steamid: str
    steamid64: str
    level: int
    avatar: str

    class Config:
        model = models.MatchSpectator
        model_fields = ['id']

    @staticmethod
    def resolve_steamid(obj):
        return steamid64_to_hex(obj.user.account.steamid)

    @staticmethod
    def resolve_steamid64(obj):
        return obj.user.account.steamid

    @staticmethod
    def resolve_level(obj):
        return obj.user.account.level

    @staticmethod
    def resolve_username(obj):
        return obj.user.account.username

    @staticmethod
    def resolve_avatar(obj):
        return Steam.build_avatar_url(obj.user.steam_user.avatarhash, 'medium')


class MatchTeamFiveMSchema(ModelSchema):
    players: List[MatchTeamPlayerFiveMSchema] = []

    class Config:
        model = models.MatchTeam
        model_fields = ['name']

    @staticmethod
    def resolve_players(obj):
        return [player.user for player in obj.players]


class MatchFiveMSchema(ModelSchema):
    match_id: int = Field(None, alias='id')
    teams: List[MatchTeamFiveMSchema]
    specs: List[MatchSpecFiveMSchema] = []
    match_type: str
    map: int

    class Config:
        model = models.Match
        model_fields = ['game_mode', 'restricted_weapon']

    @staticmethod
    def resolve_map(obj):
        return obj.map.id

    @staticmethod
    def resolve_specs(obj):
        return obj.matchspectator_set.all()


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
    map_image: str = None
    match_type: str
    game_mode: str
    start_date: str
    end_date: str
    won: bool
    score: str
    stats: MatchListItemStatsSchema


class MatchCreationSchema(Schema):
    players_ids: List[int]
    mode: str = models.Match.GameMode.COMPETITIVE
    map_id: int = None
    weapon: str = None
    def_players_ids: List[int] = []
    atk_players_ids: List[int] = []
    spec_players_ids: List[int] = []

    @root_validator
    def validations(cls, values):
        pid_count = len(values.get('players_ids'))

        if values.get('mode') == models.Match.GameMode.COMPETITIVE:
            if pid_count < 10:
                raise ValueError(_('Invalid number of players.'))
        else:
            dpid_count = len(values.get('def_players_ids'))
            apid_count = len(values.get('atk_players_ids'))
            spid_count = len(values.get('spec_players_ids'))
            total_custom_ids = dpid_count + apid_count + spid_count

            if (dpid_count == 0 and apid_count == 0) or total_custom_ids != pid_count:
                raise ValueError(_('Invalid number of players.'))

        return values

    @validator('mode')
    def check_mode(cls, value):
        if value not in models.Match.GameMode.__members__.values():
            raise ValueError(_('Invalid mode.'))

        return value

    @validator('map_id')
    def check_map_id(cls, value):
        if value:
            try:
                models.Map.objects.get(id=value)
            except models.Map.DoesNotExist:
                raise ValueError(_('Invalid map id.'))

        return value

    @validator('weapon')
    def check_weapon(cls, value):
        if value and value not in models.Match.WeaponChoices.__members__.values():
            raise ValueError(_('Invalid weapon.'))

        return value
