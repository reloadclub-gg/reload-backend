from __future__ import annotations

import random
from datetime import datetime
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import RedisClient
from core.utils import str_to_timezone

cache = RedisClient()
User = get_user_model()


class PlayerException(Exception):
    pass


class Player(BaseModel):
    """
    This model represents players on Redis cache db.
    The Redis db keys from this model are described below:

    [set] __mm:players <user_id: int>
    [set] __mm:player:[user_id]:dodges <timezone: str>
    [set] __mm:player:[user_id]:queue_lock <int>
    """

    user_id: int

    class Config:
        CACHE_PREFIX: str = '__mm:player'
        DODGES_EXPIRE_TIME = settings.PLAYER_DODGES_EXPIRE_TIME
        DODGES_MULTIPLIER = [1, 5, 10, 15, 20, 40, 60, 90]
        DODGES_MAX = len(DODGES_MULTIPLIER)
        DODGES_MAX_TIME = 604800  # 1 week

    @property
    def cache_key(self) -> str:
        """
        Model key repr on Redis.
        """
        return f'{self.Config.CACHE_PREFIX}:{self.user_id}'

    @property
    def dodges(self) -> int:
        return cache.zcard(f'{self.cache_key}:dodges')

    @property
    def latest_dodge(self) -> str:
        if self.dodges > 0:
            return str_to_timezone(
                cache.zrevrangebyscore(
                    f'{self.cache_key}:dodges', '+inf', '-inf', start=0, num=1
                )[0]
            )

    @staticmethod
    def create(user_id: int) -> Player:
        cache.sadd('__mm:players', user_id)
        return Player(user_id=user_id)

    @staticmethod
    def get_all() -> List[Player]:
        return [
            Player(user_id=int(user_id)) for user_id in cache.smembers('__mm:players')
        ]

    @staticmethod
    def get_by_user_id(user_id: int):
        if cache.sismember('__mm:players', user_id):
            return Player(user_id=user_id)

        raise PlayerException(_('Player not found'))

    def dodge_add(self):
        cache.zadd(
            f'{self.cache_key}:dodges',
            {timezone.now().isoformat(): timezone.now().timestamp()},
        )
        cache.expire(f'{self.cache_key}:dodges', Player.Config.DODGES_EXPIRE_TIME)

        if self.dodges >= Player.Config.DODGES_MAX:
            cache.incr(f'{self.cache_key}:queue_lock', Player.Config.DODGES_MAX_TIME)
        elif self.dodges > 2:
            lock_time = self.dodges * Player.Config.DODGES_MULTIPLIER.get(self.dodges)
            cache.incr(f'{self.cache_key}:queue_lock', lock_time)

    def dodge_clear(self):
        cache.delete(f'{self.cache_key}:dodges')
