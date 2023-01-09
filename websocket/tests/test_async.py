from channels.layers import get_channel_layer

from accounts.tests.mixins import Random3HundredsAccountsMixin
from core.tests import TestCase


class WSAsyncTestCase(Random3HundredsAccountsMixin, TestCase):
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
