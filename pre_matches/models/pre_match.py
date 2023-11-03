from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import TextChoices
from django.utils import timezone
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import redis_client_instance as cache
from core.utils import str_to_timezone

from .team import Team

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
    [key] __mm:pre_match:[id]:ready_time str
    [set] __mm:pre_match:[id]:ready_players_ids <(player_id,...)>
    [set] __mm:pre_match:[id]:in_players_ids <(player_id,...)>
    [key] __mm:pre_match:[id]:status str
    """

    id: int

    class Config:
        CACHE_PREFIX: str = '__mm:pre_match:'
        READY_COUNTDOWN: int = settings.MATCH_READY_COUNTDOWN
        READY_COUNTDOWN_GAP: int = settings.MATCH_READY_COUNTDOWN_GAP

    class Status(TextChoices):
        LOCK_IN = 'lock_in'
        READY_IN = 'ready_in'
        READY = 'ready'

    @property
    def cache_key(self) -> str:
        return f'{PreMatch.Config.CACHE_PREFIX}{self.id}'

    @property
    def status(self) -> str:
        return cache.get(f'{self.cache_key}:status')

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

        def transaction_operations(pipe, pre_result):
            auto_id = PreMatch.incr_auto_id()
            pipe.set(
                f'{PreMatch.Config.CACHE_PREFIX}{auto_id}',
                f'{team1_id}:{team2_id}',
            )
            pipe.set(
                f'{PreMatch.Config.CACHE_PREFIX}{auto_id}:status',
                PreMatch.Status.LOCK_IN,
            )

            pipe.set(f'{team1.cache_key}:pre_match', auto_id)
            pipe.set(f'{team2.cache_key}:pre_match', auto_id)
            return auto_id

        auto_id = cache.protected_handler(
            transaction_operations,
            f'{team1.cache_key}',
            f'{team1.cache_key}:ready',
            f'{team1.cache_key}:pre_match',
            f'{team2.cache_key}',
            f'{team2.cache_key}:ready',
            f'{team2.cache_key}:pre_match',
            value_from_callable=True,
        )

        return PreMatch.get_by_id(auto_id)

    @staticmethod
    def get_by_id(id: int, fail_silently=False):
        """
        Searchs for a match given an id.
        """
        cache_key = f'{PreMatch.Config.CACHE_PREFIX}{id}'
        result = cache.get(cache_key)
        if not result:
            if fail_silently:
                return None
            raise PreMatchException(_('PreMatch not found.'))
        return PreMatch(id=id)

    @staticmethod
    def get_by_team_id(team1_id: str, team2_id: str = None):
        keys = list(cache.scan_keys(f'{PreMatch.Config.CACHE_PREFIX}*'))
        if not keys:
            return None

        values = cache.mget(keys)

        for key, value in zip(keys, values):
            match_id = key.split(':')[2]
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
        keys = list(cache.scan_keys(f'{PreMatch.Config.CACHE_PREFIX}*'))
        if not keys:
            return []

        filtered_keys = [key for key in keys if len(key.split(':')) == 3]
        return [PreMatch.get_by_id(key.split(':')[2]) for key in filtered_keys]

    @staticmethod
    def get_by_player_id(player_id: int):
        for pre_match in PreMatch.get_all():
            players_ids = [player.id for player in pre_match.players]
            if player_id in players_ids:
                return pre_match

        return None

    def start_players_ready_countdown(self):
        self.set_status_ready_in()
        cache.set(f'{self.cache_key}:ready_time', timezone.now().isoformat())

    def set_status_ready_in(self):
        if self.status != PreMatch.Status.LOCK_IN:
            raise PreMatchException(_('PreMatch is not ready to lock in players.'))

        cache.set(f'{self.cache_key}:status', PreMatch.Status.READY_IN)

    def set_status_ready(self):
        cache.set(f'{self.cache_key}:status', PreMatch.Status.READY)

    def set_player_ready(self, user_id: int):
        if self.status != PreMatch.Status.READY_IN:
            raise PreMatchException(_('PreMatch is not ready for ready players.'))

        cache.sadd(f'{self.cache_key}:ready_players_ids', user_id)

        if len(self.players_ready) >= len(self.players):
            self.set_status_ready()

    def set_player_lock_in(self, user_id: int):
        if self.status != PreMatch.Status.LOCK_IN:
            raise PreMatchException(_('PreMatch is not ready to lock in players.'))

        cache.sadd(f'{self.cache_key}:in_players_ids', user_id)

        if len(self.players_in) >= len(self.players):
            self.start_players_ready_countdown()

    @staticmethod
    def delete_cache_keys(keys, pipe=None):
        if pipe:
            pipe.delete(*keys)
        else:
            cache.delete(*keys)

    @staticmethod
    def delete(id: int, pipe=None):
        pre_match = PreMatch.get_by_id(id, fail_silently=True)
        if pre_match:
            keys = list(cache.scan_keys(f'{pre_match.cache_key}:*'))
            t1, t2 = pre_match.teams
            team_keys = []

            if t1:
                team_keys.append(f'{t1.cache_key}:pre_match')

            if t2:
                team_keys.append(f'{t2.cache_key}:pre_match')

            keys.append(pre_match.cache_key)
            PreMatch.delete_cache_keys(keys, pipe)

            if team_keys:
                PreMatch.delete_cache_keys(team_keys, pipe)
