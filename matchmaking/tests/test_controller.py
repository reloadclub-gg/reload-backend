from datetime import datetime
from unittest import mock

from ninja.errors import HttpError

from core.tests import TestCase

from ..api import controller
from ..models import Lobby
from . import mixins


class LobbyControllerTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

    def test_lobby_remove_player(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        lobby_1.invite(lobby_1.id, lobby_2.id)
        Lobby.move(lobby_2.id, self.user_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

        controller.lobby_remove_player(
            lobby_id=lobby_1.id,
            user_id=self.user_2.id,
        )

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_lobby_invite(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        controller.lobby_invite(
            lobby_id=lobby_1.id,
            from_user_id=self.user_1.id,
            to_user_id=self.user_2.id,
        )

        self.assertEqual(lobby_1.invites, [f'{self.user_1.id}:{self.user_2.id}'])

    def test_lobby_refuse_invite(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_2.invite(lobby_2.id, lobby_1.id)

        self.assertListEqual(lobby_2.invites, [f'{self.user_2.id}:{self.user_1.id}'])
        self.assertEqual(lobby_1.players_count, 1)

        controller.lobby_refuse_invite(
            lobby_id=lobby_2.id, invite_id=f'{self.user_2.id}:{self.user_1.id}'
        )

        self.assertListEqual(lobby_1.invites, [])
        self.assertEqual(lobby_1.players_count, 1)

    def test_lobby_refuse_invite_with_raise(self):
        lobby = Lobby.create(self.user_1.id)

        with self.assertRaises(HttpError):
            controller.lobby_refuse_invite(lobby_id=lobby.id, invite_id='99:99')

    def test_lobby_change_type_and_mode(self):
        lobby = Lobby.create(self.user_1.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        controller.lobby_change_type_and_mode(lobby.id, 'custom', 20)

        self.assertEqual(lobby.mode, 20)
        self.assertEqual(lobby.lobby_type, 'custom')

    @mock.patch(
        'matchmaking.models.Lobby.queue',
        return_value=datetime.now(),
    )
    def test_lobby_change_type_and_mode_with_set_type_exception(self, _mock):
        lobby = Lobby.create(self.user_1.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        with self.assertRaises(HttpError):
            controller.lobby_change_type_and_mode(lobby.id, 'custom', 20)

    def test_lobby_enter(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_1.set_public()
        lobby_2 = Lobby.create(self.user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        controller.lobby_enter(self.user_2, lobby_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

    def test_lobby_enter_isnt_public(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        with self.assertRaises(HttpError):
            controller.lobby_enter(self.user_2, lobby_1.id)

    def test_set_public(self):
        lobby = Lobby.create(self.user_1.id)
        lobby_returned = controller.set_public(lobby.id)

        self.assertEqual(lobby_returned, lobby)
        self.assertTrue(lobby.is_public)

    def test_set_private(self):
        lobby = Lobby.create(self.user_1.id)
        lobby_returned = controller.set_private(lobby.id)

        self.assertEqual(lobby_returned, lobby)
        self.assertFalse(lobby.is_public)

    def test_lobby_leave(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_2.invite(self.user_2.id, self.user_1.id)

        Lobby.move(self.user_1.id, lobby_2.id)

        self.assertEqual(lobby_1.players_count, 0)
        self.assertEqual(lobby_2.players_count, 2)

        controller.lobby_leave(self.user_1)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_lobby_start_queue(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertFalse(lobby.queue)

        controller.lobby_start_queue(lobby.id)

        self.assertTrue(lobby.queue)

    def test_lobby_start_queue_with_queued(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertFalse(lobby.queue)
        lobby.start_queue()

        with self.assertRaises(HttpError):
            controller.lobby_start_queue(lobby.id)

    def test_lobby_cancel_queue(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.start_queue()
        self.assertTrue(lobby.queue)

        controller.lobby_cancel_queue(lobby.id)

        self.assertFalse(lobby.queue)
