from channels.testing import WebsocketCommunicator

from accounts.tests.mixins import VerifiedAccountMixin
from core.tests import TestCase
from websocket.consumers import JsonAuthWebsocketConsumer


class WSConsumerTestCase(VerifiedAccountMixin, TestCase):
    def __create_ws_comm(self) -> WebsocketCommunicator:
        self.user.auth.create_token()
        communicator = WebsocketCommunicator(
            JsonAuthWebsocketConsumer.as_asgi(),
            f'/test/?token={self.user.auth.token}',
        )
        return communicator

    async def test_communicator(self):
        communicator = self.__create_ws_comm()
        connected, _ = await communicator.connect()
        assert connected
        await communicator.disconnect()

    # TODO: Review this test to make it work (https://github.com/3C-gg/reload-backend/issues/384).
    # async def test_consumer(self):
    #     communicator = self.__create_ws_comm()
    #     await communicator.connect()
    #     payload = {'hello': 'world'}
    #     await communicator.send_json_to(payload)
    #     message = await communicator.receive_json_from()
    #     self.assertEqual(payload, message)
    #     await communicator.disconnect()
