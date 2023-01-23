from __future__ import annotations

import secrets

from django.contrib.auth import get_user_model
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
    ERRORS = {
        'not_found': 'Team not found.',
    }


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

    lobbies_ids: list
    id: str = None
    cache_key: str = None

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.id or secrets.token_urlsafe(TeamConfig.ID_SIZE)
        self.cache_key = self.cache_key or f'{TeamConfig.CACHE_PREFIX}{self.id}'

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
        return bool(cache.get(f'{self.cache_key}:ready'))

    def save(self) -> Team:
        """
        Save team into Redis db.
        """
        cache.sadd(self.cache_key, *self.lobbies_ids)
        return self

    def delete(self):
        """
        Delete team from Redis db.
        """
        cache.delete(self.cache_key)

    def set_ready(self):
        """
        Save a ready key for the team on Redis db.
        """
        cache.set(f'{self.cache_key}:ready', 1)

    def set_not_ready(self):
        """
        Delete the ready key for the team on Redis db.
        """
        cache.delete(f'{self.cache_key}:ready')

    @staticmethod
    def get_by_id(id: str) -> Team:
        """
        Searchs for a team given an ID.
        """
        cache_key = f'{TeamConfig.CACHE_PREFIX}{id}'
        lobbies_ids = list(cache.smembers(cache_key))
        if not lobbies_ids:
            raise TeamException(TeamConfig.ERRORS['not_found'])

        return Team(id=id, lobbies_ids=lobbies_ids)

    @staticmethod
    def build(lobby: Lobby) -> Team:
        """
        Look for queued lobbies that are compatible
        and put them together in a team.
        """
        # check whether the lobby is queued
        if lobby.queue:

            team = Team(lobbies_ids=[lobby.id])

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
                        min_overall, max_overall = lobby.get_overall_by_elapsed_time()
                        if min_overall <= other_lobby.overall <= max_overall:
                            team.lobbies_ids.append(other_lobby.id)
                            team.save()
                            if team.players_count == lobby.max_players:
                                team.set_ready()

            return team
