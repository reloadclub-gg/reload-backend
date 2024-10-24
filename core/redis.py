from collections.abc import Callable

from django.conf import settings
from redis import ConnectionPool, Redis, exceptions

pool = ConnectionPool(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    username=settings.REDIS_USERNAME,
    password=settings.REDIS_PASSWORD,
    db=settings.REDIS_TEST_DB if settings.TEST_MODE else settings.REDIS_APP_DB,
    decode_responses=True,
    socket_timeout=2,
)


class RedisClient(Redis):
    TRANSACTION_MAX_RETRIES_DEFAULT = 3

    class RetryException(Exception):
        pass

    def __init__(self):
        super().__init__(
            connection_pool=pool,
            charset='utf-8',
            ssl=settings.REDIS_SSL,
        )

    def protected_handler(self, func: Callable, *watches, **kwargs):
        """
        Convenience method for executing the callable `func` as a transaction
        while watching all keys specified in `watches`. The 'func' callable
        should expect a single argument which is a Pipeline object.
        """
        value_from_callable = kwargs.pop('value_from_callable', False)
        max_retries = kwargs.pop('max_retries', self.TRANSACTION_MAX_RETRIES_DEFAULT)
        pre_func = kwargs.pop('pre_func', None)
        with self.pipeline(transaction=False) as pipe:
            for _ in range(max_retries):
                try:
                    pipe.watch(*watches)
                    pre_func_value = None
                    if callable(pre_func):
                        pre_func_value = pre_func(pipe)
                    pipe.multi()
                    func_value = func(pipe, pre_func_value)
                    exec_value = pipe.execute()
                    return func_value if value_from_callable else exec_value
                except exceptions.WatchError:
                    pass
            else:
                raise self.RetryException(
                    f'Concurrency reached maximum of {max_retries} retries.'
                )

    def scan_keys(self, pattern: str, count: int = 100):
        cursor = '0'
        while cursor != 0:
            cursor, keys = self.scan(cursor=cursor, match=pattern, count=count)
            for key in keys:
                yield key


redis_client_instance = RedisClient()
