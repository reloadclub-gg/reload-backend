from channels.testing import WebsocketCommunicator

from accounts.tests.mixins import VerifiedAccountMixin
from core.tests import TestCase
from websocket.consumers import JsonAuthWebsocketConsumer


class WSConsumerTestCase(VerifiedAccountMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user.auth.create_token()
        self.user.account

    async def test_connect(self):
        communicator = WebsocketCommunicator(
            JsonAuthWebsocketConsumer.as_asgi(), f'/?token={self.user.auth.token}'
        )
        connected, subprotocol = await communicator.connect()
        assert connected
