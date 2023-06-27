from asgiref.sync import sync_to_async

from accounts.api.schemas import FriendAccountSchema
from accounts.tests.mixins import UserWithFriendsMixin
from core.tests import TestCase
from lobbies.api.schemas import LobbySchema
from lobbies.models import Lobby
from websocket import controller


class WSControllerTestCase(UserWithFriendsMixin, TestCase):
    def __create_lobbies(self):
        self.user.auth.add_session()
        self.friend1.auth.add_session()
        self.friend2.auth.add_session()
        return [
            Lobby.create(self.user.id),
            Lobby.create(self.friend1.id),
            Lobby.create(self.friend2.id),
        ]

    def __get_schema_dict(self, schema, obj):
        return schema.from_orm(obj).dict()

    async def test_user_status_change(self):
        data = await sync_to_async(controller.user_status_change)(self.user)

        expected_payload = await sync_to_async(self.__get_schema_dict)(
            FriendAccountSchema, self.user.account
        )

        self.assertEqual(data.get('payload'), expected_payload)
        self.assertEqual(data.get('meta').get('action'), 'ws_userStatusChange')

    async def test_lobby_update(self):
        lobbies = await sync_to_async(self.__create_lobbies)()
        results = await sync_to_async(controller.lobby_update)(lobbies)
        self.assertEqual(len(results), len(lobbies))
        expected_payload = await sync_to_async(self.__get_schema_dict)(
            LobbySchema, lobbies[0]
        )
        assert any(data.get('payload') == expected_payload for data in results)
