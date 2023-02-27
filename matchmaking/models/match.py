from __future__ import annotations

import secrets

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import RedisClient

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


class Match(BaseModel):
    """
    This model represents matches on Redis cache db.
    Match is a platform match and not a FiveM match.
    This model has all necessary logic and properties that
    need to be done before create a REAL match on FiveM and disk db.

    The Redis db keys from this model are described below:

    [set] __mm:match:[match_id] <team_1_id, team_2_id>
    Stores a match.
    """

    team_1_id: int
    team_2_id: int
    id: str = None
    cache_key: str = None

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.id or secrets.token_urlsafe(MatchConfig.ID_SIZE)
        self.cache_key = self.cache_key or f'{MatchConfig.CACHE_PREFIX}{self.id}'
