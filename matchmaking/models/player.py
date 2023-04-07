from __future__ import annotations

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
    [set] __mm:player:[user_id]:queue_lock <timezone: str>
    """

    user_id: int

    class Config:
        CACHE_PREFIX: str = '__mm:player'
        DODGES_EXPIRE_TIME = settings.PLAYER_DODGES_EXPIRE_TIME
        DODGES_MULTIPLIER = [1, 5, 10, 15, 20, 40, 60, 90]
        DODGES_MAX = len(DODGES_MULTIPLIER)
        DODGES_MAX_TIME = 604800  # 1 week in minutes

    @property
    def cache_key(self) -> str:
        """
        Model key repr on Redis.
        """
        return f'{self.Config.CACHE_PREFIX}:{self.user_id}'

    @property
    def dodges(self) -> int:
        """
        Return how many match dodges player has in last week.
        """
        return cache.zcard(f'{self.cache_key}:dodges')

    @property
    def latest_dodge(self) -> timezone.datetime:
        """
        Return the latest player match dodge.
        """
        if self.dodges > 0:
            return str_to_timezone(
                cache.zrevrangebyscore(
                    f'{self.cache_key}:dodges', '+inf', '-inf', start=0, num=1
                )[0]
            )

    @property
    def lock_date(self) -> timezone.datetime:
        """
        Return the timezone date when queue restriction will end,
        if this player has a restriction.
        """
        queue_lock = cache.get(f'{self.cache_key}:queue_lock')
        if queue_lock:
            return str_to_timezone(queue_lock)

    @property
    def lock_countdown(self) -> int:
        """
        Return the countdown, in seconds, for the queue restriction end.
        """
        if self.lock_date:
            return (self.lock_date - timezone.now()).seconds

    @staticmethod
    def create(user_id: int) -> Player:
        """
        Creates a player entry on Redis db and return a Player instance.
        """
        cache.sadd('__mm:players', user_id)
        return Player(user_id=user_id)

    @staticmethod
    def get_all() -> List[Player]:
        """
        Fetches all players on Redis db.
        """
        return [
            Player(user_id=int(user_id)) for user_id in cache.smembers('__mm:players')
        ]

    @staticmethod
    def get_by_user_id(user_id: int) -> Player:
        """
        Searches for a Player with the given user_id and returns it.
        """
        if cache.sismember('__mm:players', user_id):
            return Player(user_id=user_id)

        raise PlayerException(_('Player not found'))

    def dodge_add(self) -> timezone.datetime:
        """
        Add a new dodge datetime on Redis db.

        Each time a player dodges a match, the dodges set will receive a new entry, and its ttl
        will be renewed.

        When a player reaches 3 dodges in a week (Player.Config.DODGES_EXPIRE_TIME), this method
        creates a queue_lock entry on Redis for that player. This entry holds the datetime when the
        restriction ends. This entry restricts the player from queueing again on whatever lobby
        he is until the restriction is over.
        """

        if self.lock_date:
            raise PlayerException(_('Player cannot dodge while in queue restriction.'))

        cache.zadd(
            f'{self.cache_key}:dodges',
            {timezone.now().isoformat(): timezone.now().timestamp()},
        )
        cache.expire(f'{self.cache_key}:dodges', Player.Config.DODGES_EXPIRE_TIME)

        if self.dodges >= Player.Config.DODGES_MAX:
            delta = timezone.timedelta(minutes=Player.Config.DODGES_MAX_TIME)
            lock_date = timezone.now() + delta
            cache.set(
                f'{self.cache_key}:queue_lock',
                lock_date.isoformat(),
                ex=delta,
            )
            return lock_date
        elif self.dodges > 2:
            multiplier = Player.Config.DODGES_MULTIPLIER[self.dodges - 2]
            lock_minutes = self.dodges * multiplier
            delta = timezone.timedelta(minutes=lock_minutes)
            lock_date = timezone.now() + delta
            cache.set(
                f'{self.cache_key}:queue_lock',
                lock_date.isoformat(),
                ex=delta,
            )
            return lock_date

    def dodge_clear(self):
        """
        Clear all dodges from a player.
        Should be called every week (7 days).
        """
        cache.delete(f'{self.cache_key}:dodges')

    @staticmethod
    def delete(user_id: int):
        """
        Delete player from the players set on Redis.
        This should be called upon a player logout.
        """
        player = Player.get_by_user_id(user_id=user_id)
        cache.srem('__mm:players', player.user_id)
