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
        'canceled': -2,
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

    [key] __mm:match:[match_id] [team1_id:team2_id]
    Stores a match with teams ids.

    [key] __mm:match:[match_id]:ready_time
    Stores the datetime that a match was ready for players to confirm their seats.

    [set] __mm:match:[match_id]:ready_players_ids
    Stores which players are ready.

    [key] __mm:match:[match_id]:players_in
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
            self.countdown is not None
            and self.countdown >= PreMatchConfig.READY_COUNTDOWN_GAP
            and len(self.players_ready) < PreMatchConfig.READY_PLAYERS_MIN
        ):
            return PreMatchConfig.STATES.get('lock_in')
        elif len(self.players_ready) == PreMatchConfig.READY_PLAYERS_MIN:
            return PreMatchConfig.STATES.get('ready')
        elif (
            self.countdown is not None
            and self.countdown <= PreMatchConfig.READY_COUNTDOWN_GAP
            and len(self.players_ready) < PreMatchConfig.READY_PLAYERS_MIN
        ):
            return PreMatchConfig.STATES.get('canceled')
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
    def players_ready(self) -> list[User]:
        if self.countdown and self.countdown > 0:
            players_ids = cache.smembers(f'{self.cache_key}:ready_players_ids')
            if players_ids:
                return [User.objects.get(pk=player_id) for player_id in players_ids]

        return []

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
        return PreMatch(id=id)

    @staticmethod
    def get_by_team_id(team1_id: str, team2_id: str = None):
        matches_keys = cache.keys(f'{PreMatchConfig.CACHE_PREFIX}*')
        for key in matches_keys:
            match_id = key.split(':')[2]
            value = cache.get(key)
            if team2_id:
                if value == f'{team1_id}:{team2_id}':
                    return PreMatch(id=match_id)
            else:
                if team1_id in value:
                    return PreMatch(id=match_id)

    @staticmethod
    def get_all():
        pre_matches_keys = cache.keys(f'{PreMatchConfig.CACHE_PREFIX}*')
        result = []
        for pre_match_key in pre_matches_keys:
            pre_match_id = pre_match_key.split(':')[2]
            pre_match = PreMatch.get_by_id(pre_match_id)
            result.append(pre_match)

        return result

    @staticmethod
    def get_by_player_id(player_id: int):
        for pre_match in PreMatch.get_all():
            players_ids = [player.id for player in pre_match.players]
            if player_id in players_ids:
                return pre_match

        return None

    def start_players_ready_countdown(self):
        cache.set(f'{self.cache_key}:ready_time', timezone.now().isoformat())

    def set_player_ready(self, user_id: int):
        if not self.state == PreMatchConfig.STATES.get('lock_in'):
            raise PreMatchException(_('PreMatch is not ready for ready players.'))

        cache.sadd(f'{self.cache_key}:ready_players_ids', user_id)

    def set_player_lock_in(self):
        if not self.state == PreMatchConfig.STATES.get('pre_start'):
            raise PreMatchException(_('PreMatch is not ready to lock in players.'))

        cache.incr(f'{self.cache_key}:players_in')

    @staticmethod
    def delete(id: str, pipe=None):
        pre_match = PreMatch(id=id)
        keys = cache.keys(f'{pre_match.cache_key}:*')
        if len(keys) >= 1:
            if pipe:
                pipe.delete(*keys)
                pipe.delete(pre_match.cache_key)
            else:
                cache.delete(*keys)
                cache.delete(pre_match.cache_key)
