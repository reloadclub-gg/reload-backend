from unittest import mock

from ninja.errors import AuthenticationError, Http404, HttpError

from core.tests import TestCase
from matchmaking.models import Team
from matchmaking.tests.mixins import VerifiedPlayersMixin

from ..api import controller, schemas
from ..models import Lobby, LobbyInvite


class LobbyControllerTestCase(VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()
        self.user_7.auth.add_session()
        Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)
        Lobby.create(self.user_6.id)
        Lobby.create(self.user_7.id)

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    @mock.patch('lobbies.api.controller.ws_friend_update_or_create')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.ws_update_lobby_id')
    def test_player_move_single_to_group(
        self,
        mock_update_lobby_id,
        mock_update_player,
        mock_friend_update,
        mock_update_lobby,
    ):
        self.user_1.account.lobby.set_public()
        controller.player_move(self.user_2, self.user_1.account.lobby.id)
        mock_calls = [
            mock.call(Lobby(owner_id=self.user_2.id), self.user_2, 'leave'),
            mock.call(self.user_1.account.lobby, self.user_2, 'join'),
        ]
        mock_update_player.assert_has_calls(mock_calls)
        self.assertEqual(mock_update_lobby_id.call_count, 1)
        self.assertEqual(mock_update_lobby.call_count, 1)
        self.assertEqual(mock_friend_update.call_count, 2)

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    @mock.patch('lobbies.api.controller.ws_friend_update_or_create')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.ws_update_lobby_id')
    def test_player_move_group_to_group(
        self,
        mock_update_lobby_id,
        mock_update_player,
        mock_friend_update,
        mock_update_lobby,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)

        self.user_3.account.lobby.invite(self.user_3.id, self.user_2.id)
        controller.player_move(self.user_2, self.user_3.account.lobby.id)

        mock_calls = [
            mock.call(self.user_1.account.lobby, self.user_2, 'leave'),
            mock.call(self.user_3.account.lobby, self.user_2, 'join'),
        ]
        mock_update_player.assert_has_calls(mock_calls)
        self.assertEqual(mock_update_lobby_id.call_count, 1)
        self.assertEqual(mock_update_lobby.call_count, 1)
        mock_friend_update.assert_called_once_with(self.user_1)

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    @mock.patch('lobbies.api.controller.ws_friend_update_or_create')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.ws_update_lobby_id')
    def test_player_move_group_owner_to_group(
        self,
        mock_update_lobby_id,
        mock_update_player,
        mock_friend_update,
        mock_update_lobby,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        self.user_5.account.lobby.invite(self.user_5.id, self.user_1.id)
        controller.player_move(self.user_1, self.user_5.account.lobby.id)

        self.assertEqual(mock_update_lobby_id.call_count, 4)
        self.assertEqual(mock_update_lobby.call_count, 4)
        mock_calls = [
            mock.call(Lobby(owner_id=self.user_2.id), self.user_1, 'leave'),
            mock.call(Lobby(owner_id=self.user_1.id), self.user_1, 'leave'),
            mock.call(self.user_5.account.lobby, self.user_1, 'join'),
        ]
        mock_update_player.assert_has_calls(mock_calls)
        mock_friend_update.assert_called_once_with(self.user_5)

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    @mock.patch('lobbies.api.controller.ws_friend_update_or_create')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.ws_update_lobby_id')
    def test_player_move_group_owner_to_single(
        self,
        mock_update_lobby_id,
        mock_update_player,
        mock_friend_update,
        mock_update_lobby,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        controller.player_move(self.user_1, self.user_1.account.lobby.id)

        mock_update_player.assert_called_once()
        self.assertEqual(mock_update_lobby_id.call_count, 4)
        self.assertEqual(mock_update_lobby.call_count, 5)
        mock_friend_update.assert_called_once_with(self.user_1)

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    @mock.patch('lobbies.api.controller.ws_friend_update_or_create')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.ws_update_lobby_id')
    def test_player_move_group_to_single(
        self,
        mock_update_lobby_id,
        mock_update_player,
        mock_friend_update,
        mock_update_lobby,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        controller.player_move(self.user_2, self.user_2.id)

        mock_calls = [
            mock.call(Lobby(owner_id=self.user_1.id), self.user_2, 'leave'),
            mock.call(self.user_2.account.lobby, self.user_2, 'join'),
        ]
        mock_update_player.assert_has_calls(mock_calls)
        self.assertEqual(mock_update_lobby_id.call_count, 1)
        self.assertEqual(mock_update_lobby.call_count, 1)
        mock_friend_update.assert_called_once_with(self.user_2)

    def test_player_move_error(self):
        with self.assertRaises(HttpError):
            controller.player_move(self.user_2, self.user_1.id)

    def test_get_lobby(self):
        lobby = controller.get_lobby(self.user_1.account.lobby.id)
        self.assertIsNotNone(lobby)
        self.assertEqual(lobby.id, self.user_1.account.lobby.id)
        self.assertEqual(lobby.owner_id, self.user_1.id)

    def test_get_user_invites(self):
        self.user_1.account.lobby.invite(self.user_1.id, self.user_2.id)
        self.user_3.account.lobby.invite(self.user_3.id, self.user_2.id)
        self.user_4.account.lobby.invite(self.user_4.id, self.user_1.id)

        invites = controller.get_user_invites(self.user_1)
        self.assertEqual(len(invites), 2)

        invites = controller.get_user_invites(self.user_1, sent=True)
        self.assertEqual(len(invites), 1)

        invites = controller.get_user_invites(self.user_1, received=True)
        self.assertEqual(len(invites), 1)

        invites = controller.get_user_invites(self.user_2)
        self.assertEqual(len(invites), 2)

        invites = controller.get_user_invites(self.user_2, sent=True)
        self.assertEqual(len(invites), 0)

        invites = controller.get_user_invites(self.user_2, received=True)
        self.assertEqual(len(invites), 2)

    def test_get_invite(self):
        created = self.user_1.account.lobby.invite(self.user_1.id, self.user_2.id)
        invite = controller.get_invite(self.user_1, created.id)
        self.assertEqual(invite.id, created.id)

    def test_get_invite_invalid_id(self):
        with self.assertRaises(HttpError):
            controller.get_invite(self.user_1, 'some_id')

    def test_get_invite_unauthorized(self):
        created = self.user_1.account.lobby.invite(self.user_1.id, self.user_2.id)
        with self.assertRaises(AuthenticationError):
            controller.get_invite(self.user_3, created.id)

    def test_get_invite_not_found(self):
        with self.assertRaises(Http404):
            controller.get_invite(self.user_1, f'{self.user_1.id}:2')

    @mock.patch('lobbies.api.controller.websocket.ws_create_invite')
    def test_create_invite(self, mock_create_invite):
        created = controller.create_invite(
            self.user_1,
            schemas.LobbyInviteCreateSchema.from_orm(
                {
                    'lobby_id': self.user_1.account.lobby.id,
                    'from_user_id': self.user_1.id,
                    'to_user_id': self.user_2.id,
                }
            ),
        )

        invite = LobbyInvite.get_by_id(created.id)
        self.assertIsNotNone(invite)
        self.assertEqual(invite.id, created.id)
        mock_create_invite.assert_called_once_with(invite)

    @mock.patch('lobbies.api.controller.websocket.ws_create_invite')
    def test_create_invite_unauthorized_other_user(self, mock_create_invite):
        payload = schemas.LobbyInviteCreateSchema.from_orm(
            {
                'lobby_id': self.user_3.account.lobby.id,
                'from_user_id': self.user_3.id,
                'to_user_id': self.user_2.id,
            }
        )
        with self.assertRaises(AuthenticationError):
            controller.create_invite(self.user_1, payload)

        mock_create_invite.assert_not_called()

    @mock.patch('lobbies.api.controller.websocket.ws_create_invite')
    def test_create_invite_unauthorized_wrong_lobby(self, mock_create_invite):
        payload = schemas.LobbyInviteCreateSchema.from_orm(
            {
                'lobby_id': self.user_3.account.lobby.id,
                'from_user_id': self.user_1.id,
                'to_user_id': self.user_2.id,
            }
        )
        with self.assertRaises(AuthenticationError):
            controller.create_invite(self.user_1, payload)

        mock_create_invite.assert_not_called()

    @mock.patch('lobbies.api.controller.websocket.ws_delete_invite')
    @mock.patch('lobbies.api.controller.player_move')
    def test_accept_invite(
        self,
        mock_player_move,
        mock_delete_invite,
    ):
        created = self.user_1.account.lobby.invite(self.user_1.id, self.user_2.id)
        controller.accept_invite(self.user_2, created.id)
        mock_delete_invite.assert_called_once()
        mock_player_move.assert_called_once()

    def test_accept_invite_unauthorized(self):
        created = self.user_1.account.lobby.invite(self.user_1.id, self.user_2.id)
        with self.assertRaises(AuthenticationError):
            controller.accept_invite(self.user_3, created.id)

    @mock.patch('lobbies.api.controller.websocket.ws_delete_invite')
    def test_refuse_invite(
        self,
        mock_delete_invite,
    ):
        created = self.user_1.account.lobby.invite(self.user_1.id, self.user_2.id)
        controller.refuse_invite(self.user_2, created.id)
        mock_delete_invite.assert_called_once()

    @mock.patch('lobbies.api.controller.player_move')
    def test_delete_player(self, mock_player_move):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)

        controller.delete_player(
            self.user_2,
            self.user_1.account.lobby.id,
            self.user_2.id,
        )

        mock_player_move.assert_called_once_with(self.user_2, self.user_2.id)

    @mock.patch('lobbies.api.controller.player_move')
    def test_delete_player_same_lobby(self, mock_player_move):
        controller.delete_player(
            self.user_1,
            self.user_1.account.lobby.id,
            self.user_1.id,
        )
        mock_player_move.assert_not_called()

    @mock.patch('lobbies.api.controller.player_move')
    def test_delete_player_kick(self, mock_player_move):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)

        controller.delete_player(
            self.user_1,
            self.user_1.account.lobby.id,
            self.user_2.id,
        )
        mock_player_move.assert_called_once_with(self.user_2, self.user_2.id)

    def test_delete_player_kick_unauthorized(self):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)

        with self.assertRaises(AuthenticationError):
            controller.delete_player(
                self.user_2,
                self.user_1.account.lobby.id,
                self.user_3.id,
            )

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_update_lobby_start_queue_owner(self, mock_update_lobby):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        payload = schemas.LobbyUpdateSchema.from_orm({'start_queue': True})

        self.assertIsNone(self.user_1.account.lobby.queue)
        controller.update_lobby(
            self.user_1,
            self.user_1.account.lobby.id,
            payload,
        )
        self.assertIsNotNone(self.user_1.account.lobby.queue)
        mock_update_lobby.assert_called_once_with(self.user_1.account.lobby)

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_update_lobby_start_queue_unauthorized(self, mock_update_lobby):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        payload = schemas.LobbyUpdateSchema.from_orm({'start_queue': True})

        with self.assertRaises(AuthenticationError):
            controller.update_lobby(
                self.user_2,
                self.user_1.account.lobby.id,
                payload,
            )

        mock_update_lobby.assert_not_called()

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_update_lobby_start_queue_error(self, mock_update_lobby):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        self.user_1.account.lobby.start_queue()

        payload = schemas.LobbyUpdateSchema.from_orm({'start_queue': True})
        with self.assertRaises(HttpError):
            controller.update_lobby(
                self.user_1,
                self.user_1.account.lobby.id,
                payload,
            )

        mock_update_lobby.assert_not_called()

    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_update_lobby_cancel_queue(self, mock_update_lobby):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        payload = schemas.LobbyUpdateSchema.from_orm({'start_queue': True})
        controller.update_lobby(
            self.user_1,
            self.user_1.account.lobby.id,
            payload,
        )

        self.assertIsNotNone(self.user_1.account.lobby.queue)
        payload = schemas.LobbyUpdateSchema.from_orm({'cancel_queue': True})
        controller.update_lobby(
            self.user_1,
            self.user_1.account.lobby.id,
            payload,
        )
        self.assertIsNone(self.user_1.account.lobby.queue)

        payload = schemas.LobbyUpdateSchema.from_orm({'start_queue': True})
        controller.update_lobby(
            self.user_1,
            self.user_1.account.lobby.id,
            payload,
        )

        self.assertIsNotNone(self.user_1.account.lobby.queue)
        payload = schemas.LobbyUpdateSchema.from_orm({'cancel_queue': True})
        controller.update_lobby(
            self.user_2,
            self.user_1.account.lobby.id,
            payload,
        )
        self.assertIsNone(self.user_1.account.lobby.queue)
        mock_update_lobby.assert_any_call(self.user_1.account.lobby)
        self.assertEqual(mock_update_lobby.call_count, 4)

    @mock.patch('lobbies.api.controller.ws_match_found')
    def test_handle_match_found(self, mock_match_found):
        with self.settings(TEAM_READY_PLAYERS_MIN=1):
            self.user_1.account.lobby.start_queue()
            team1 = Team.find(self.user_1.account.lobby) or Team.build(
                self.user_1.account.lobby
            )
            self.user_2.account.lobby.start_queue()
            team2 = Team.find(self.user_2.account.lobby) or Team.build(
                self.user_2.account.lobby
            )

            controller.handle_match_found(team1, team2)
            mock_match_found.assert_called_once()

    @mock.patch('lobbies.api.controller.handle_match_found')
    def test_update_lobby_start_queue_match_found(self, mock_match_found):
        payload = schemas.LobbyUpdateSchema.from_orm({'start_queue': True})

        with self.settings(TEAM_READY_PLAYERS_MIN=1):
            controller.update_lobby(
                self.user_1,
                self.user_1.account.lobby.id,
                payload,
            )

            controller.update_lobby(
                self.user_2,
                self.user_2.account.lobby.id,
                payload,
            )

            mock_match_found.assert_called_once()
