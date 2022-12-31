from unittest import mock
from datetime import datetime
from ninja.errors import HttpError
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

    def test_lobby_refuse_invite(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_2.invite(lobby_1.id)

        self.assertListEqual(lobby_2.invites, [lobby_1.id])
        self.assertEqual(lobby_1.players_count, 1)

        controller.lobby_refuse_invite(
            user=self.online_verified_user_1, lobby_id=lobby_2.id
        )

        self.assertListEqual(lobby_1.invites, [])
        self.assertEqual(lobby_1.players_count, 1)

    def test_lobby_change_type_and_mode(self):
        lobby = Lobby.create(self.online_verified_user_1.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        controller.lobby_change_type_and_mode(
            self.online_verified_user_1, lobby.id, 'custom', 20
        )

        self.assertEqual(lobby.mode, 20)
        self.assertEqual(lobby.lobby_type, 'custom')

    def test_lobby_change_type_and_mode_by_non_owner(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        with self.assertRaisesMessage(
            HttpError, 'User must be owner to perfom this action'
        ):
            controller.lobby_change_type_and_mode(
                self.online_verified_user_2, lobby.id, 'custom', 20
            )

    @mock.patch(
        'matchmaking.models.Lobby.queue',
        return_value=datetime.now(),
    )
    def test_lobby_change_type_and_mode_with_set_type_exception(self, _mock):
        lobby = Lobby.create(self.online_verified_user_1.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        with self.assertRaisesMessage(
            HttpError, 'Lobby is queued caught on set lobby type'
        ):
            controller.lobby_change_type_and_mode(
                self.online_verified_user_1, lobby.id, 'custom', 20
            )

    def test_lobby_enter(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_1.set_public()
        lobby_2 = Lobby.create(self.online_verified_user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        controller.lobby_enter(self.online_verified_user_2, lobby_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

    def test_lobby_enter_isnt_public(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        with self.assertRaisesMessage(
            HttpError, 'User not invited caught on lobby move'
        ):
            controller.lobby_enter(self.online_verified_user_2, lobby_1.id)
