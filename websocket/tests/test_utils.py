import asyncio
from threading import Thread

from channels.layers import get_channel_layer
from django.conf import settings

from accounts.tests.mixins import AccountOneMixin
from core.tests import TestCase
from websocket import utils

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


class WSUtilsTestCase(AccountOneMixin, TestCase):
    async def listen1(self):
        channel_layer = get_channel_layer()
        message = await channel_layer.receive(f'{settings.GROUP_NAME_PREFIX}.group1')
        assert message['type'] == 'send_payload'
        assert message['payload'] == {'content': 'test'}
        assert message['meta']['action'] == 'ws_Test'
        assert 'timestamp' in message['meta']

    async def listen2(self):
        channel_layer = get_channel_layer()
        message = await channel_layer.receive(f'{settings.GROUP_NAME_PREFIX}.group2')
        assert message['type'] == 'send_payload'
        assert message['payload'] == {'content': 'test'}
        assert message['meta']['action'] == 'ws_Test'
        assert 'timestamp' in message['meta']

    def between_callback(self):
        loop.run_until_complete(self.listen1())
        loop.run_until_complete(self.listen2())

    async def test_ws_send(self):
        channel_layer = get_channel_layer()

        thread1 = Thread(target=self.between_callback)
        thread1.start()

        await utils.ws_send(
            'ws_Test',
            {'content': 'test'},
            ['group1', 'group2'],
        )

        await channel_layer.flush()
