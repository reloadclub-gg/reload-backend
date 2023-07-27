from __future__ import annotations

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


class PreMatch(BaseModel):
    """
    This model represents a pre-match on Redis cache db.
    This model has all necessary logic and properties that
    need to be done before create a REAL match on FiveM and disk db.

    The Redis db keys from this model are described below:

    [key] __mm:pre_match__auto_id int

    [key] __mm:pre_match:[id] [team1_id:team2_id]
    Stores a pre_match with teams ids.

    [key] __mm:pre_match:[id]:ready_time
    Stores the datetime that a pre_match was ready for players to confirm their seats.

    [set] __mm:pre_match:[id]:ready_players_ids
    Stores which players are ready.

    [set] __mm:pre_match:[id]:in_players_ids
    Stores which locked in players are in pre_match.
    """

    id: int

    class Config:
        CACHE_PREFIX: str = '__mm:pre_match:'
        ID_SIZE: int = 16
        READY_COUNTDOWN: int = settings.MATCH_READY_COUNTDOWN
        READY_COUNTDOWN_GAP: int = settings.MATCH_READY_COUNTDOWN_GAP
        STATES = {
            'canceled': -2,
            'idle': -1,
            'pre_start': 0,
            'lock_in': 1,
            'ready': 2,
        }

    @property
    def cache_key(self) -> str:
        return f'{PreMatch.Config.CACHE_PREFIX}{self.id}'

    @property
    def state(self) -> str:
        if len(self.players_in) < len(self.players):
            return PreMatch.Config.STATES.get('pre_start')
        elif (
            self.countdown is not None
            and self.countdown > PreMatch.Config.READY_COUNTDOWN_GAP
            and len(self.players_ready) < len(self.players)
        ):
            return PreMatch.Config.STATES.get('lock_in')
        elif len(self.players_ready) == len(self.players):
            return PreMatch.Config.STATES.get('ready')
        elif (
            self.countdown is not None
            and self.countdown <= PreMatch.Config.READY_COUNTDOWN_GAP
            and len(self.players_ready) < len(self.players)
        ):
            return PreMatch.Config.STATES.get('canceled')
        else:
            return PreMatch.Config.STATES.get('idle')

    @property
    def countdown(self) -> int:
        ready_start_time = cache.get(f'{self.cache_key}:ready_time')
        if ready_start_time:
            ready_start_time = str_to_timezone(ready_start_time)
            elapsed_time = (timezone.now() - ready_start_time).seconds
            return PreMatch.Config.READY_COUNTDOWN - elapsed_time

    @property
    def players_ready(self) -> list[User]:
        players_ids = cache.smembers(f'{self.cache_key}:ready_players_ids')
        if players_ids:
            return User.objects.filter(pk__in=players_ids)

        return []

    @property
    def players_in(self) -> int:
        players_ids = cache.smembers(f'{self.cache_key}:in_players_ids')
        if players_ids:
            return User.objects.filter(pk__in=players_ids)

        return []

    @property
    def teams(self) -> tuple[Team]:
        team1 = Team.get_by_id(cache.get(self.cache_key).split(':')[0])
        team2 = Team.get_by_id(cache.get(self.cache_key).split(':')[1])
        return (team1, team2)

    @property
    def team1_players(self) -> list[User]:
        if not self.teams[0]:
            return []

        lobbies = self.teams[0].lobbies
        player_ids = [player_id for lobby in lobbies for player_id in lobby.players_ids]
        return list(User.objects.filter(id__in=player_ids))

    @property
    def team2_players(self) -> list[User]:
        if not self.teams[1]:
            return []

        lobbies = self.teams[1].lobbies
        player_ids = [player_id for lobby in lobbies for player_id in lobby.players_ids]
        return list(User.objects.filter(id__in=player_ids))

    @property
    def players(self) -> list[User]:
        return self.team1_players + self.team2_players

    @staticmethod
    def incr_auto_id() -> int:
        return int(cache.incr('__mm:pre_match__auto_id'))

    @staticmethod
    def get_auto_id() -> int:
        count = cache.get('__mm:pre_match__auto_id')
        return int(count) if count else 0

    @staticmethod
    def create(team1_id: str, team2_id: str) -> PreMatch:
        team1 = Team.get_by_id(team1_id)
        team2 = Team.get_by_id(team2_id)

        if not any([team1.ready, team2.ready]):
            raise PreMatchException(
                _('All teams must be ready in order to create a PreMatch.')
            )

        auto_id = PreMatch.incr_auto_id()
        cache.set(
            f'{PreMatch.Config.CACHE_PREFIX}{auto_id}',
            f'{team1_id}:{team2_id}',
        )

        cache.set(f'{team1.cache_key}:pre_match', auto_id)
        cache.set(f'{team2.cache_key}:pre_match', auto_id)
        return PreMatch.get_by_id(auto_id)

    @staticmethod
    def get_by_id(id: int):
        """
        Searchs for a match given an id.
        """
        cache_key = f'{PreMatch.Config.CACHE_PREFIX}{id}'
        result = cache.get(cache_key)
        if not result:
            raise PreMatchException(_('PreMatch not found.'))
        return PreMatch(id=id)

    @staticmethod
    def get_by_team_id(team1_id: str, team2_id: str = None):
        matches_keys = cache.keys(f'{PreMatch.Config.CACHE_PREFIX}*')
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
    def get_all() -> list[Team]:
        """
        Fetch and return all PreMatches on Redis db.
        """
        all_keys = cache.keys(f'{PreMatch.Config.CACHE_PREFIX}*')
        result = []
        for key in all_keys:
            if len(key.split(':')) == 3:
                result.append(key)

        return [PreMatch.get_by_id(key.split(':')[2]) for key in result]

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
        if not self.state == PreMatch.Config.STATES.get('lock_in'):
            raise PreMatchException(_('PreMatch is not ready for ready players.'))

        cache.sadd(f'{self.cache_key}:ready_players_ids', user_id)

    def set_player_lock_in(self, user_id: int):
        if not self.state == PreMatch.Config.STATES.get('pre_start'):
            raise PreMatchException(_('PreMatch is not ready to lock in players.'))

        cache.sadd(f'{self.cache_key}:in_players_ids', user_id)

    @staticmethod
    def delete(id: int, pipe=None):
        pre_match = PreMatch(id=id)
        keys = cache.keys(f'{pre_match.cache_key}:*')
        if len(keys) >= 1:
            if pipe:
                pipe.delete(*keys)
                pipe.delete(pre_match.cache_key)
            else:
                cache.delete(*keys)
                cache.delete(pre_match.cache_key)
