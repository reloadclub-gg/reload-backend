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


class MatchException(Exception):
    """
    Custom Match exception class.
    """

    pass


class MatchConfig:
    """
    Config class for the Match model.
    """

    CACHE_PREFIX: str = '__mm:match:'
    ID_SIZE: int = 16
    READY_COUNTDOWN: int = settings.MATCH_READY_COUNTDOWN
    READY_COUNTDOWN_GAP: int = settings.MATCH_READY_COUNTDOWN_GAP
    READY_PLAYERS_MIN: int = settings.MATCH_READY_PLAYERS_MIN
    STATES = {
        'pre_start': 0,
        'lock_in': 1,
        'ready': 2,
    }


class Match(BaseModel):
    """
    This model represents matches on Redis cache db.
    Match is a platform match and not a FiveM match.
    This model has all necessary logic and properties that
    need to be done before create a REAL match on FiveM and disk db.

    The Redis db keys from this model are described below:

    [key] __mm:match:[match_id] <str> [team1_id:team2_id]
    Stores a match with teams ids.

    [key] __mm:match:[match_id]:ready_time <datetime>
    Stores the datetime that a match was ready for players to confirm their seats.

    [key] __mm:match:[match_id]:ready_count <int>
    Holds the amount of players that are ready to play before we create the Match.

    [key] __mm:match:[match_id]:players_in <int>
    Holds the amount of players that are in the pre match so the countdown of ready starts.
    """

    id: str = None
    cache_key: str = None

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.id or secrets.token_urlsafe(MatchConfig.ID_SIZE)
        self.cache_key = self.cache_key or f'{MatchConfig.CACHE_PREFIX}{self.id}'

    @property
    def state(self) -> str:
        if self.countdown is None and self.ready_players == 0:
            return MatchConfig.STATES.get('pre_start')
        elif (
            self.countdown >= MatchConfig.READY_COUNTDOWN_GAP
            and self.ready_players < MatchConfig.READY_PLAYERS_MIN
        ):
            return MatchConfig.STATES.get('lock_in')
        else:
            return MatchConfig.STATES.get('ready')

    @property
    def countdown(self) -> int:
        ready_start_time = cache.get(f'{self.cache_key}:ready_time')
        if ready_start_time:
            ready_start_time = str_to_timezone(ready_start_time)
            elapsed_time = (timezone.now() - ready_start_time).seconds
            return MatchConfig.READY_COUNTDOWN - elapsed_time

    @property
    def ready_players(self) -> int:
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
    def create(team1_id: str, team2_id: str) -> Match:
        team1 = Team.get_by_id(team1_id)
        team2 = Team.get_by_id(team2_id)

        if not any([team1.ready, team2.ready]):
            raise MatchException(
                _('All teams must be ready in order to create a Match.')
            )

        match_id = secrets.token_urlsafe(MatchConfig.ID_SIZE)
        cache.set(f'{MatchConfig.CACHE_PREFIX}{match_id}', f'{team1_id}:{team2_id}')
        return Match.get_by_id(match_id)

    @staticmethod
    def get_by_id(id: str):
        """
        Searchs for a match given an id.
        """
        cache_key = f'{MatchConfig.CACHE_PREFIX}{id}'
        result = cache.get(cache_key)
        if not result:
            raise MatchException(_('Match not found.'))

        team1_id = result.split(':')[0]
        team2_id = result.split(':')[1]
        return Match(team1_id=team1_id, team2_id=team2_id, id=id)

    def start_players_ready_countdown(self):
        cache.set(f'{self.cache_key}:ready_time', timezone.now().isoformat())

    def set_player_ready(self):
        if not self.state == MatchConfig.STATES.get('lock_in'):
            raise MatchException(_('Match is not ready for ready players.'))

        cache.incr(f'{self.cache_key}:ready_count')

    def set_player_lock_in(self):
        if not self.state == MatchConfig.STATES.get('pre_start'):
            raise MatchException(_('Match is not ready to lock in players.'))

        cache.incr(f'{self.cache_key}:players_in')
