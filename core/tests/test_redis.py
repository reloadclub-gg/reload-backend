from threading import Thread

from django.utils import timezone

from core.redis import RedisClient

from . import TestCase

cache = RedisClient()


class TestWatchError(TestCase):
    def setUp(self) -> None:
        cache.set('__mm:lobby:1', '1')
        cache.set('__mm:lobby:1:queue', '2022-04-28T18:21:17.852892+00:00')
        cache.sadd('__mm:lobby:1:players', '1')
        cache.sadd('__mm:lobby:1:players', '2')
        cache.sadd('__mm:lobby:1:players', '3')
        return super().setUp()

    def noise(self):
        cache.sadd('__mm:lobby:1:players', '4')

    def multi_noise(self):
        cache.zadd('__mm:lobby:1:invites', {'4': timezone.now().timestamp()})

    def test_single_watching_key(self):
        def transaction_operations(pipe, _):
            thread = Thread(target=self.noise)
            thread.start()
            pipe.set('__mm:lobby:1:queue', timezone.now().isoformat())
            thread.join()

        with self.assertRaisesRegex(
            Exception, 'Concurrency reached maximum of 1 retries.'
        ):
            cache.protected_handler(
                transaction_operations,
                '__mm:lobby:1:players',
                max_retries=1,
            )

        self.assertEqual(
            '2022-04-28T18:21:17.852892+00:00', cache.get('__mm:lobby:1:queue')
        )

    def test_multiple_watching_key(self):
        def transaction_operations(pipe, _):
            thread = Thread(target=self.multi_noise)
            thread.start()
            pipe.set('__mm:lobby:1:queue', timezone.now().isoformat())
            thread.join()

        with self.assertRaisesRegex(
            Exception, 'Concurrency reached maximum of 1 retries.'
        ):
            cache.protected_handler(
                transaction_operations,
                '__mm:lobby:1:players',
                '__mm:lobby:1:invites',
                max_retries=1,
            )

        self.assertEqual(
            '2022-04-28T18:21:17.852892+00:00', cache.get('__mm:lobby:1:queue')
        )

    def test_watching_returning_value(self):
        def transaction_pre(pipe):
            return pipe.smembers('__mm:lobby:1:players')

        def transaction_operations(pipe, pre_result):
            pipe.set('__mm:lobby:1:queue', timezone.now().isoformat())

            return {'status': 'ok'}

        return cache.protected_handler(
            transaction_operations,
            '__mm:lobby:1:players',
            max_retries=1,
            pre_func=transaction_pre,
            value_from_callable=True,
        )
