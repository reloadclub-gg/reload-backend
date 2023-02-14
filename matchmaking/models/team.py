from __future__ import annotations

import secrets
from math import ceil
from statistics import mean

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import RedisClient

from .lobby import Lobby

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
    MAX_PLAYERS_COUNT: int = 5


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
        return self.players_count == TeamConfig.MAX_PLAYERS_COUNT

    @property
    def overall(self) -> int:
        """
        Return all lobbies overall.
        """
        return ceil(
            mean([Lobby(owner_id=lobby_id).overall for lobby_id in self.lobbies_ids])
        )

    @property
    def challengeable(self) -> list[Team]:
        ready = Team.get_all_ready()
        # for team in ready:
        #     min_overall, max_overall = lobby.get_min_max_overall_by_queue_time()
        #     if min_overall <= other_lobby.overall <= max_overall:

    @staticmethod
    def get_all() -> list[Team]:
        """
        Fetch and return all Teams on Redis db.
        """
        teams_keys = cache.keys(f'{TeamConfig.CACHE_PREFIX}*')
        return [Team.get_by_id(team_key.split(':')[2]) for team_key in teams_keys]

    @staticmethod
    def get_all_not_ready() -> Team:
        """
        Fetch all non ready teams in Redis db.
        """
        teams = Team.get_all()
        return [team for team in teams if not team.ready]

    @staticmethod
    def get_all_ready() -> Team:
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

        if players_count > TeamConfig.MAX_PLAYERS_COUNT:
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
                min_overall, max_overall = lobby.get_min_max_overall_by_queue_time()
                if min_overall <= team.overall <= max_overall:
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

    def challenge(self):
        ready_teams = self.get_all_ready()
