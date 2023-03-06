from __future__ import annotations

import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import RedisClient
from core.utils import str_to_timezone

from .team import Team

cache = RedisClient()
User = get_user_model()


class PreMatchException(Exception):
    """
    Custom PreMatch exception class.
    """

    pass


class PreMatchConfig:
    """
    Config class for the PreMatch model.
    """

    CACHE_PREFIX: str = '__mm:match:'
    ID_SIZE: int = 16
    READY_COUNTDOWN: int = settings.MATCH_READY_COUNTDOWN
    READY_COUNTDOWN_GAP: int = settings.MATCH_READY_COUNTDOWN_GAP
    READY_PLAYERS_MIN: int = settings.MATCH_READY_PLAYERS_MIN
    STATES = {
        'idle': -1,
        'pre_start': 0,
        'lock_in': 1,
        'ready': 2,
    }


class PreMatch(BaseModel):
    """
    This model represents a pre-match on Redis cache db.
    This model has all necessary logic and properties that
    need to be done before create a REAL match on FiveM and disk db.

    The Redis db keys from this model are described below:

    [key] __mm:match:[match_id] <str> [team1_id:team2_id]
    Stores a match with teams ids.

    [key] __mm:match:[match_id]:ready_time <datetime>
    Stores the datetime that a match was ready for players to confirm their seats.

    [key] __mm:match:[match_id]:ready_count <int>
    Holds the amount of players that are ready to play before we create the PreMatch.

    [key] __mm:match:[match_id]:players_in <int>
    Holds the amount of players that are in the pre match so the countdown of ready starts.
    """

    id: str = None
    cache_key: str = None

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.id or secrets.token_urlsafe(PreMatchConfig.ID_SIZE)
        self.cache_key = self.cache_key or f'{PreMatchConfig.CACHE_PREFIX}{self.id}'

    @property
    def state(self) -> str:
        if self.players_in < PreMatchConfig.READY_PLAYERS_MIN:
            return PreMatchConfig.STATES.get('pre_start')
        elif (
            self.countdown
            and self.countdown >= PreMatchConfig.READY_COUNTDOWN_GAP
            and self.players_ready < PreMatchConfig.READY_PLAYERS_MIN
        ):
            return PreMatchConfig.STATES.get('lock_in')
        elif self.players_ready == PreMatchConfig.READY_PLAYERS_MIN:
            return PreMatchConfig.STATES.get('ready')
        else:
            return PreMatchConfig.STATES.get('idle')

    @property
    def countdown(self) -> int:
        ready_start_time = cache.get(f'{self.cache_key}:ready_time')
        if ready_start_time:
            ready_start_time = str_to_timezone(ready_start_time)
            elapsed_time = (timezone.now() - ready_start_time).seconds
            return PreMatchConfig.READY_COUNTDOWN - elapsed_time

    @property
    def players_ready(self) -> int:
        if self.countdown and self.countdown > 0:
            count = cache.get(f'{self.cache_key}:ready_count')
            if count:
                return int(count)

        return 0

    @property
    def players_in(self) -> int:
        count = cache.get(f'{self.cache_key}:players_in')
        if count:
            return int(count)

        return 0

    @property
    def teams(self) -> tuple[Team]:
        team1 = Team.get_by_id(cache.get(self.cache_key).split(':')[0])
        team2 = Team.get_by_id(cache.get(self.cache_key).split(':')[1])
        return (team1, team2)

    @property
    def team1_players(self) -> list[User]:
        lobbies = self.teams[0].lobbies
        players = []
        for lobby in lobbies:
            players += [
                User.objects.get(id=player_id) for player_id in lobby.players_ids
            ]
        return players

    @property
    def team2_players(self) -> list[User]:
        lobbies = self.teams[1].lobbies
        players = []
        for lobby in lobbies:
            players += [
                User.objects.get(id=player_id) for player_id in lobby.players_ids
            ]
        return players

    @property
    def players(self) -> list[User]:
        return self.team1_players + self.team2_players

    @staticmethod
    def create(team1_id: str, team2_id: str) -> PreMatch:
        team1 = Team.get_by_id(team1_id)
        team2 = Team.get_by_id(team2_id)

        if not any([team1.ready, team2.ready]):
            raise PreMatchException(
                _('All teams must be ready in order to create a PreMatch.')
            )

        match_id = secrets.token_urlsafe(PreMatchConfig.ID_SIZE)
        cache.set(f'{PreMatchConfig.CACHE_PREFIX}{match_id}', f'{team1_id}:{team2_id}')
        return PreMatch.get_by_id(match_id)

    @staticmethod
    def get_by_id(id: str):
        """
        Searchs for a match given an id.
        """
        cache_key = f'{PreMatchConfig.CACHE_PREFIX}{id}'
        result = cache.get(cache_key)
        if not result:
            raise PreMatchException(_('PreMatch not found.'))

        team1_id = result.split(':')[0]
        team2_id = result.split(':')[1]
        return PreMatch(team1_id=team1_id, team2_id=team2_id, id=id)

    def start_players_ready_countdown(self):
        cache.set(f'{self.cache_key}:ready_time', timezone.now().isoformat())

    def set_player_ready(self):
        if not self.state == PreMatchConfig.STATES.get('lock_in'):
            raise PreMatchException(_('PreMatch is not ready for ready players.'))

        cache.incr(f'{self.cache_key}:ready_count')

    def set_player_lock_in(self):
        if not self.state == PreMatchConfig.STATES.get('pre_start'):
            raise PreMatchException(_('PreMatch is not ready to lock in players.'))

        cache.incr(f'{self.cache_key}:players_in')
