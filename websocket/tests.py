from channels.layers import get_channel_layer

from django.conf import settings

from accounts.models.auth import AuthConfig
from accounts.tests.mixins import AccountOneMixin, Random3HundredsAccountsMixin
from core.tests import TestCase
from . import auth, utils


class WSAuthTestCase(AccountOneMixin, TestCase):
    def setUp(self) -> None:
        self.user.account.is_verified = True
        self.user.account.save()
        self.user.auth.create_token()
        return super().setUp()

    def test_authenticate(self):
        scope = {'query_string': f'anyurl.com/?token={self.user.auth.token}'}
        user = auth.authenticate(scope)
        self.assertEqual(self.user.id, user.id)
        self.assertEqual(self.user.auth.sessions_ttl, -1)

    def test_authenticate_fail(self):
        scope = {'query_string': '?token=any_token'}
        user = auth.authenticate(scope)
        self.assertIsNone(user)

    def test_disconnect(self):
        self.user.auth.add_session()
        auth.disconnect(self.user)
        self.assertEqual(self.user.auth.sessions_ttl, AuthConfig.CACHE_TTL_SESSIONS)

        self.user.auth.expire_session(0)
        self.user.auth.add_session()
        self.user.auth.add_session()
        auth.disconnect(self.user)
        self.assertEqual(self.user.auth.sessions, 1)
        self.assertEqual(self.user.auth.sessions_ttl, -1)


class WSCoreTestCase(Random3HundredsAccountsMixin, TestCase):
    def setUp(self) -> None:
        self.user = self.random_verified()
        self.user2 = self.random_verified(exclude=[self.user.id])
        self.user.auth.create_token()
        self.user2.auth.create_token()
        return super().setUp()

    async def test_send_and_receive(self):

        channel_layer = get_channel_layer()

        # Aioredis connections can't be used from different event loops, so
        # send and close need to be done in the same async_to_sync call.
        async def send_and_close(*args, **kwargs):
            await channel_layer.send(*args, **kwargs)
            await channel_layer.close_pools()

        channel_name_1 = await channel_layer.new_channel()
        channel_name_2 = await channel_layer.new_channel()
        await send_and_close(channel_name_1, {'type': 'test.message.1'})
        await send_and_close(channel_name_2, {'type': 'test.message.2'})

        # Make things to listen on the loops
        async def listen1():
            message = await channel_layer.receive(channel_name_1)
            assert message['type'] == 'test.message.1'
            await channel_layer.close_pools()

        async def listen2():
            message = await channel_layer.receive(channel_name_2)
            assert message['type'] == 'test.message.2'
            await channel_layer.close_pools()

        # Run them inside threads
        await listen2()
        await listen1()
        # Clean up
        await channel_layer.flush()


class WSUtilsTestCase(AccountOneMixin, TestCase):
    async def test_ws_send(self):
        channel_layer = get_channel_layer()
        channel_name_1 = await channel_layer.new_channel()
        channel_name_2 = await channel_layer.new_channel()

        await utils.ws_send(
            'ws_Test',
            {'content': 'test'},
            [channel_name_1, channel_name_2],
        )

        async def listen1():
            message = await channel_layer.receive(
                f'{settings.GROUP_NAME_PREFIX}.{channel_name_1}'
            )
            assert message['type'] == 'send_payload'
            assert message['payload'] == {'content': 'test'}
            assert message['meta']['action'] == 'ws_Test'
            assert 'timestamp' in message['meta']
            await channel_layer.close_pools()

        async def listen2():
            message = await channel_layer.receive(
                f'{settings.GROUP_NAME_PREFIX}.{channel_name_2}'
            )
            assert message['type'] == 'send_payload'
            assert message['payload'] == {'content': 'test'}
            assert message['meta']['action'] == 'ws_Test'
            assert 'timestamp' in message['meta']
            await channel_layer.close_pools()

        await listen2()
        await listen1()
        await channel_layer.flush()
