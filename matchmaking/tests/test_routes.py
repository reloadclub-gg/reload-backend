from core.tests import APIClient, TestCase
from ..models import Lobby
from . import mixins


class LobbyLeaveTestCase(mixins.SomePlayersMixin, TestCase):
    def setUp(self) -> None:
        self.api = APIClient('/api/mm')
        super().setUp()
        self.online_verified_user_1.auth.add_session()
        self.online_verified_user_1.auth.create_token()
        self.online_verified_user_2.auth.add_session()

    def test_lobby_leave(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_2.invite(self.online_verified_user_1.id)

        Lobby.move(self.online_verified_user_1.id, lobby_2.id)

        self.assertEqual(lobby_1.players_count, 0)
        self.assertEqual(lobby_2.players_count, 2)

        response = self.api.call(
            'get', '/lobby/leave', token=self.online_verified_user_1.auth.token
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)
