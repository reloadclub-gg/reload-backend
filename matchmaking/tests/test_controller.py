from core.tests import TestCase
from . import mixins
from ..api import controller
from ..models import Lobby


class LobbyControllerTestCase(mixins.SomePlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.online_verified_user_1.auth.add_session()
        self.online_verified_user_2.auth.add_session()

    def test_lobby_remove(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)

        lobby_1.invite(lobby_2.id)
        Lobby.move(lobby_2.id, self.online_verified_user_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

        controller.lobby_remove(
            request_user_id=self.online_verified_user_1.id,
            lobby_id=lobby_1.id,
            user_id=self.online_verified_user_2.id,
        )

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_lobby_invite(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        controller.lobby_invite(
            user=self.online_verified_user_1,
            lobby_id=lobby_1.id,
            player_id=self.online_verified_user_2.id,
        )

        self.assertEqual(lobby_1.invites, [lobby_2.id])
