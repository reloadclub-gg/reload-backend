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
