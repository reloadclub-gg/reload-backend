from __future__ import annotations

import random
import secrets
from math import ceil
from statistics import mean

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import RedisClient
from lobbies.models import Lobby

cache = RedisClient()
User = get_user_model()


class TeamException(Exception):
    """
    Custom Team exception class.
    """

    pass


class TeamConfig:
    """
    Config class for the Team model.
    """

    CACHE_PREFIX: str = '__mm:team:'
    ID_SIZE: int = 16
    READY_PLAYERS_MIN: int = settings.TEAM_READY_PLAYERS_MIN


class Team(BaseModel):
    """
    This model represents teams on Redis cache db.
    Teams are full lobbies that are queued.

    The Redis db keys from this model are described below:

    [set] __mm:team:[team_id] <lobby_ids>
    Stores a team.

    [key] __mm:team:[team_id]:ready 1
    If this key exists, the team is ready and able to find an
    oposing team to play against. A team is ready when it reaches
    the maximum numbers of players.
    """

    id: str = None
    cache_key: str = None

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.id or secrets.token_urlsafe(TeamConfig.ID_SIZE)
        self.cache_key = self.cache_key or f'{TeamConfig.CACHE_PREFIX}{self.id}'

    @property
    def lobbies_ids(self) -> list:
        return sorted(list(map(int, cache.smembers(self.cache_key))))

    @property
    def players_count(self) -> int:
        """
        Return how many players are in all the team lobbies.
        """
        return sum(
            [Lobby(owner_id=lobby_id).players_count for lobby_id in self.lobbies_ids]
        )

    @property
    def ready(self) -> bool:
        """
        Return whether this team is ready to find a oposing team.
        """
        return self.players_count == TeamConfig.READY_PLAYERS_MIN

    @property
    def overall(self) -> int:
        """
        Return all lobbies overall.

        If there is only one lobby on team, then the overral will
        be the highest level among that lobby players (what is equal to lobby.overall).

        If there is more then one lobby, the overall will be the average between all lobbies.

        This is effective because if there is only one lobby, it means that is a pre builded lobby
        with friends, and thus we want to pair by the highest skilled/leveled player.
        """
        return ceil(
            mean([Lobby(owner_id=lobby_id).overall for lobby_id in self.lobbies_ids])
        )

    @property
    def min_max_overall_by_queue_time(self) -> tuple:
        """
        Return the minimum and maximum team overall that this team
        can team up or challenge.
        """

        elapsed_time = ceil(mean([lobby.queue_time for lobby in self.lobbies]))

        if elapsed_time < 30:
            min = self.overall - 1 if self.overall > 0 else 0
            max = self.overall + 1
        elif elapsed_time < 60:
            min = self.overall - 2 if self.overall > 1 else 0
            max = self.overall + 2
        elif elapsed_time < 90:
            min = self.overall - 3 if self.overall > 2 else 0
            max = self.overall + 3
        elif elapsed_time < 120:
            min = self.overall - 4 if self.overall > 3 else 0
            max = self.overall + 4
        else:
            min = self.overall - 5 if self.overall > 4 else 0
            max = self.overall + 5

        return min, max

    @property
    def lobbies(self) -> list[Lobby]:
        """
        Return lobbies.
        """
        return [Lobby(owner_id=lobby_id) for lobby_id in self.lobbies_ids]

    @property
    def type_mode(self) -> tuple:
        """
        Return team type and mode.
        """
        return self.lobbies[0].lobby_type, self.lobbies[0].mode

    @property
    def name(self) -> str:
        """
        Return team name defined randomly between owners in lobbies
        """
        owners_ids = [lobby.owner_id for lobby in self.lobbies]
        owner_chosen_id = random.choice(owners_ids)
        return User.objects.get(pk=owner_chosen_id).steam_user.username

    @staticmethod
    def overall_match(team, lobby) -> bool:
        min_overall, max_overall = team.min_max_overall_by_queue_time
        return min_overall <= lobby.overall <= max_overall

    @staticmethod
    def get_all() -> list[Team]:
        """
        Fetch and return all Teams on Redis db.
        """
        teams_keys = cache.keys(f'{TeamConfig.CACHE_PREFIX}*')
        return [Team.get_by_id(team_key.split(':')[2]) for team_key in teams_keys]

    @staticmethod
    def get_all_not_ready() -> list[Team]:
        """
        Fetch all non ready teams in Redis db.
        """
        teams = Team.get_all()
        return [team for team in teams if not team.ready]

    @staticmethod
    def get_all_ready() -> list[Team]:
        """
        Fetch all ready teams in Redis db.
        """
        teams = Team.get_all()
        return [team for team in teams if team.ready]

    @staticmethod
    def get_by_lobby_id(lobby_id: int, fail_silently=False) -> Team:
        """
        Searchs for a team given a lobby id.
        """
        team = next(
            (team for team in Team.get_all() if lobby_id in team.lobbies_ids), None
        )
        if not team and not fail_silently:
            raise TeamException(_('Team not found.'))

        return team

    @staticmethod
    def get_by_id(id: str) -> Team:
        """
        Searchs for a team given an id.
        """
        cache_key = f'{TeamConfig.CACHE_PREFIX}{id}'
        result = cache.smembers(cache_key)
        if not result:
            raise TeamException(_('Team not found.'))

        return Team(id=id)

    @staticmethod
    def create(lobbies_ids: list) -> Team:
        """
        Create a Team in Redis cache db given a list of lobbies ids.
        """
        players_count = sum(
            [Lobby(owner_id=lobby_id).players_count for lobby_id in lobbies_ids]
        )

        if players_count > TeamConfig.READY_PLAYERS_MIN:
            raise TeamException(_('Team players count exceeded.'))

        team_id = secrets.token_urlsafe(TeamConfig.ID_SIZE)
        cache.sadd(f'{TeamConfig.CACHE_PREFIX}{team_id}', *lobbies_ids)
        return Team.get_by_id(team_id)

    @staticmethod
    def find(lobby: Lobby) -> Team:
        """
        Find a team for the given lobby.
        """
        # check if received lobby already is on a team
        teams = Team.get_all()
        if any(lobby.id in team.lobbies_ids for team in teams):
            raise TeamException(_('Lobby already on a team.'))

        # check whether the lobby is queued
        if not lobby.queue:
            raise TeamException(_('Lobby not queued.'))

        not_ready = Team.get_all_not_ready()
        for team in not_ready:
            if team.players_count + lobby.players_count <= lobby.max_players:
                # check if lobby and team type/mode matches
                if team.type_mode == (lobby.lobby_type, lobby.mode):
                    if Team.overall_match(team, lobby):
                        team.add_lobby(lobby.id)
                        return team

    @staticmethod
    def build(lobby: Lobby) -> Team:
        """
        Look for queued lobbies that are compatible
        and put them together in a team.
        """
        # check if received lobby already is on a team
        teams = Team.get_all()
        if any(lobby.id in team.lobbies_ids for team in teams):
            raise TeamException(_('Lobby already on a team.'))

        # check whether the lobby is queued
        if not lobby.queue:
            raise TeamException(_('Lobby not queued.'))

        team = Team.create(lobbies_ids=[lobby.id])

        # check if team is full already
        if team.players_count == TeamConfig.READY_PLAYERS_MIN:
            return team

        # get all queued lobbies
        lobby_ids = [
            int(key.split(':')[2])
            for key in cache.keys('__mm:lobby:*:queue')
            if lobby.id != int(key.split(':')[2])
        ]

        for lobby_id in lobby_ids:
            other_lobby = Lobby(owner_id=lobby_id)

            # check if lobbies type and mode matches
            if (
                lobby.lobby_type == other_lobby.lobby_type
                and lobby.mode == other_lobby.mode
            ):
                # check if lobbies have seats enough to merge
                total_players = team.players_count + other_lobby.players_count
                if total_players <= lobby.max_players:
                    # check if lobbies are in the same overall range
                    min_overall, max_overall = lobby.get_min_max_overall_by_queue_time()
                    if min_overall <= other_lobby.overall <= max_overall:
                        team.add_lobby(other_lobby.id)

        if len(team.lobbies_ids) > 1:
            return team
        else:
            team.delete()
            return None

    def delete(self):
        """
        Delete team from Redis db.
        """
        cache.delete(self.cache_key)

    def add_lobby(self, lobby_id: int):
        """
        Add a lobby into a Team on Redis db.
        """
        lobby = Lobby(owner_id=lobby_id)

        def transaction_operations(pipe, pre_result):
            pipe.sadd(self.cache_key, lobby_id)

        cache.protected_handler(
            transaction_operations,
            f'{lobby.cache_key}:players',
            f'{lobby.cache_key}:queue',
        )

    def remove_lobby(self, lobby_id: int):
        """
        Remove a lobby from a Team on Redis db.
        If that team was ready, then it becomes not ready.
        """
        cache.srem(self.cache_key, lobby_id)

        if len(self.lobbies_ids) <= 1:
            self.delete()

    def get_opponent_team(self):
        ready_teams = self.get_all_ready()
        for team in ready_teams:
            if self.id != team.id:
                # check if type and mode matches
                if self.type_mode == team.type_mode:
                    # check if teams are in the same overall range
                    min_overall, max_overall = team.min_max_overall_by_queue_time
                    if min_overall <= self.overall <= max_overall:
                        return team
