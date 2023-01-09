from channels.layers import get_channel_layer
from django.conf import settings

from accounts.tests.mixins import AccountOneMixin
from core.tests import TestCase
from websocket import utils


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
