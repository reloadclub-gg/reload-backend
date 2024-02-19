from typing import Optional

from django.utils.translation import gettext as _
from pydantic import BaseModel

from .redis import redis_client_instance as cache


class Q:
    def __init__(self, **kwargs):
        self.conditions = kwargs
        self.operator = 'OR'

    def __or__(self, other):
        if not isinstance(other, Q):
            raise ValueError(_('OR can only be used in Q objects'))
        return Q(**{**self.conditions, **other.conditions})

    def __and__(self, other):
        if not isinstance(other, Q):
            raise ValueError(_('AND can only be used in Q objects'))
        self.operator = 'AND'
        return Q(**{**self.conditions, **other.conditions})


class RedisBaseModel(BaseModel):
    class Config:
        CACHE_PREFIX = None

    def __init_subclass__(cls, **kwargs):
        ALLOWED_CLASSES = ['RedisBaseModel', 'RedisHashModel']

        super().__init_subclass__(**kwargs)
        if cls.__name__ not in ALLOWED_CLASSES:
            if cls.Config.CACHE_PREFIX is None:
                raise NotImplementedError(
                    _(f'{cls.__name__} must define "Config.CACHE_PREFIX".')
                )


class RedisHashModel(RedisBaseModel):
    @classmethod
    def filter(cls, *args, **kwargs) -> Optional['RedisHashModel']:
        q_conditions = [arg for arg in args if isinstance(arg, Q)]
        normal_conditions = kwargs
        result = []

        for key in cache.scan_keys(f'{cls.Config.CACHE_PREFIX}:*'):
            if key.split(':')[-1].isdigit():
                model_hash = cache.hgetall(key)
                if cls._matches_conditions(model_hash, q_conditions, normal_conditions):
                    result.append(cls(**model_hash))
        return result

    @classmethod
    def _matches_conditions(cls, model_hash, q_conditions, normal_conditions) -> bool:
        if not all(
            str(model_hash.get(k, '')) == str(v) for k, v in normal_conditions.items()
        ):
            return False

        for q in q_conditions:
            if q.operator == 'OR':
                if any(
                    str(model_hash.get(k, '')) == str(v)
                    for k, v in q.conditions.items()
                ):
                    return True
            elif q.operator == 'AND':
                if all(
                    str(model_hash.get(k, '')) == str(v)
                    for k, v in q.conditions.items()
                ):
                    return True

        return False if q_conditions else True
