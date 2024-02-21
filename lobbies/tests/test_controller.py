from unittest import mock

from django.contrib.auth import get_user_model
from ninja.errors import AuthenticationError, Http404, HttpError

from accounts.tests.mixins import VerifiedAccountsMixin
from appsettings.models import AppSettings
from core.tests import TestCase

from ..api import controller, schemas
from ..models import Lobby, LobbyException, LobbyInvite

User = get_user_model()


class LobbyControllerTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.add_session()
        self.user_2.add_session()
        self.user_3.add_session()
        self.user_4.add_session()
        self.user_5.add_session()
        self.user_6.add_session()
        self.user_7.add_session()
        Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)
        Lobby.create(self.user_6.id)
        Lobby.create(self.user_7.id)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_single_to_group(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        controller.handle_player_move(self.user_2, self.user_1.account.lobby.id)

        mock_expire_invites.assert_called_once_with(self.user_2, sent=True)
        mock_update_user.assert_called_once_with(self.user_2)

        mock_lobby_calls = [
            mock.call(Lobby(owner_id=self.user_1.id)),
            mock.call(Lobby(owner_id=self.user_2.id)),
        ]

        mock_update_player_calls = [
            mock.call(Lobby(owner_id=self.user_1.id), self.user_2, 'join'),
            mock.call(Lobby(owner_id=self.user_2.id), self.user_2, 'leave'),
        ]

        mock_update_lobby.assert_has_calls(mock_lobby_calls)
        mock_update_player.assert_has_calls(mock_update_player_calls)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_single_to_single_grouping(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()

        controller.handle_player_move(self.user_2, self.user_1.account.lobby.id)

        mock_expire_invites.assert_called_once_with(self.user_2, sent=True)

        mock_lobby_calls = [
            mock.call(Lobby(owner_id=self.user_1.id)),
            mock.call(Lobby(owner_id=self.user_2.id)),
        ]

        mock_update_player_calls = [
            mock.call(Lobby(owner_id=self.user_1.id), self.user_2, 'join'),
            mock.call(Lobby(owner_id=self.user_2.id), self.user_2, 'leave'),
        ]

        mock_update_user_calls = [
            mock.call(self.user_2),
            mock.call(self.user_1),
        ]

        mock_update_user.assert_has_calls(mock_update_user_calls)
        mock_update_lobby.assert_has_calls(mock_lobby_calls)
        mock_update_player.assert_has_calls(mock_update_player_calls)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_group_to_group_leaving_solo(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        self.user_3.account.lobby.invite(self.user_3.id, self.user_2.id)
        self.user_3.account.lobby.invite(self.user_3.id, self.user_4.id)
        Lobby.move(self.user_2.id, self.user_3.account.lobby.id)

        controller.handle_player_move(self.user_4, self.user_3.account.lobby.id)

        mock_update_lobby_calls = [
            mock.call(self.user_3.account.lobby),
            mock.call(self.user_1.account.lobby),
        ]

        mock_update_player_calls = [
            mock.call(self.user_3.account.lobby, self.user_4, 'join'),
            mock.call(self.user_1.account.lobby, self.user_4, 'leave'),
        ]

        mock_update_friend_calls = [
            mock.call(self.user_4),
            mock.call(self.user_1),
        ]

        mock_update_lobby.assert_has_calls(mock_update_lobby_calls)
        mock_update_player.assert_has_calls(mock_update_player_calls)
        mock_update_user.assert_has_calls(mock_update_friend_calls)
        mock_expire_invites.assert_called_once_with(self.user_4, sent=True)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_group_owner_to_group(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        self.user_5.account.lobby.invite(self.user_5.id, self.user_1.id)
        controller.handle_player_move(self.user_1, self.user_5.account.lobby.id)

        mock_update_lobby_calls = [
            mock.call(self.user_2.account.lobby),
            mock.call(self.user_5.account.lobby),
        ]

        mock_update_player_calls = [
            mock.call(self.user_2.account.lobby, self.user_1, 'leave'),
            mock.call(self.user_5.account.lobby, self.user_1, 'join'),
        ]

        mock_update_lobby.assert_has_calls(mock_update_lobby_calls)
        mock_update_player.assert_has_calls(mock_update_player_calls)
        self.assertEqual(mock_update_user.call_count, 5)
        self.assertEqual(mock_expire_invites.call_count, 4)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_group_owner_to_single(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        controller.handle_player_move(self.user_1, self.user_1.account.lobby.id)

        mock_update_lobby_calls = [
            mock.call(self.user_2.account.lobby),
            mock.call(self.user_1.account.lobby),
        ]

        mock_update_lobby.assert_has_calls(mock_update_lobby_calls)
        mock_update_player.assert_called_once_with(
            self.user_2.account.lobby,
            self.user_1,
            'leave',
        )
        self.assertEqual(mock_expire_invites.call_count, 4)
        self.assertEqual(mock_update_user.call_count, 4)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_group_owner_to_single_leaving_single(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)

        controller.handle_player_move(self.user_1, self.user_1.account.lobby.id)

        mock_update_lobby_calls = [
            mock.call(self.user_2.account.lobby),
            mock.call(self.user_1.account.lobby),
        ]

        mock_update_user_calls = [
            mock.call(self.user_2),
            mock.call(self.user_1),
        ]

        mock_update_lobby.assert_has_calls(mock_update_lobby_calls)
        mock_update_player.assert_called_once_with(
            self.user_2.account.lobby,
            self.user_1,
            'leave',
        )
        mock_update_user.assert_has_calls(mock_update_user_calls)
        self.assertEqual(mock_expire_invites.call_count, 2)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_group_to_single(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        controller.handle_player_move(self.user_2, self.user_2.id)

        mock_update_lobby_calls = [
            mock.call(self.user_1.account.lobby),
            mock.call(self.user_2.account.lobby),
        ]

        mock_update_lobby.assert_has_calls(mock_update_lobby_calls)
        mock_update_player.assert_called_once_with(
            self.user_1.account.lobby,
            self.user_2,
            'leave',
        )
        mock_update_user.assert_called_once_with(self.user_2)
        mock_expire_invites.assert_called_once_with(self.user_2, sent=True)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_group_to_single_leaving_single(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        controller.handle_player_move(self.user_2, self.user_2.id)

        mock_update_lobby_calls = [
            mock.call(self.user_1.account.lobby),
            mock.call(self.user_2.account.lobby),
        ]

        mock_update_user_calls = [
            mock.call(self.user_1),
            mock.call(self.user_2),
        ]

        mock_update_lobby.assert_has_calls(mock_update_lobby_calls)
        mock_update_player.assert_called_once_with(
            self.user_1.account.lobby,
            self.user_2,
            'leave',
        )
        mock_update_user.assert_has_calls(mock_update_user_calls)
        mock_expire_invites.assert_called_once_with(self.user_2, sent=True)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_group_to_single_delete(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        controller.handle_player_move(self.user_2, self.user_2.id, delete_lobby=True)

        mock_update_lobby.assert_called_once_with(self.user_1.account.lobby)
        mock_update_player.assert_called_once_with(
            self.user_1.account.lobby,
            self.user_2,
            'leave',
        )
        mock_update_user.assert_not_called()
        mock_expire_invites.assert_called_once_with(self.user_2, sent=True)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_group_owner_to_single_delete(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_3.id, self.user_1.account.lobby.id)
        Lobby.move(self.user_4.id, self.user_1.account.lobby.id)

        controller.handle_player_move(self.user_1, self.user_1.id, delete_lobby=True)

        mock_update_lobby.assert_called_once_with(self.user_2.account.lobby)
        mock_update_player.assert_called_once_with(
            self.user_2.account.lobby,
            self.user_1,
            'leave',
        )
        self.assertEqual(mock_expire_invites.call_count, 4)
        self.assertEqual(mock_update_user.call_count, 3)

    @mock.patch('lobbies.api.controller.websocket.ws_expire_player_invites')
    @mock.patch('lobbies.api.controller.ws_update_user')
    @mock.patch('lobbies.api.controller.websocket.ws_update_player')
    @mock.patch('lobbies.api.controller.websocket.ws_update_lobby')
    def test_handle_player_move_single_to_single_delete(
        self,
        mock_update_lobby,
        mock_update_player,
        mock_update_user,
        mock_expire_invites,
    ):
        controller.handle_player_move(self.user_1, self.user_1.id, delete_lobby=True)

        mock_update_lobby.assert_not_called()
        mock_update_player.assert_not_called()
        mock_update_user.assert_not_called()
        mock_expire_invites.assert_called_once_with(self.user_1, sent=True)

    def test_handle_player_move_error(self):
        with self.assertRaises(LobbyException):
            controller.handle_player_move(self.user_2, self.user_1.id)

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
    @mock.patch('lobbies.api.controller.handle_player_move')
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

    @mock.patch('lobbies.api.controller.handle_player_move')
    def test_delete_player(self, mock_player_move):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)

        controller.delete_player(
            self.user_2,
            self.user_1.account.lobby.id,
            self.user_2.id,
        )

        mock_player_move.assert_called_once_with(self.user_2, self.user_2.id)

    @mock.patch('lobbies.api.controller.handle_player_move')
    def test_delete_player_same_lobby(self, mock_player_move):
        controller.delete_player(
            self.user_1,
            self.user_1.account.lobby.id,
            self.user_1.id,
        )
        mock_player_move.assert_not_called()

    @mock.patch('lobbies.api.controller.ws_create_toast')
    @mock.patch('lobbies.api.controller.handle_player_move')
    def test_delete_player_kick(self, mock_player_move, mock_create_toast):
        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)

        controller.delete_player(
            self.user_1,
            self.user_1.account.lobby.id,
            self.user_2.id,
        )
        mock_player_move.assert_called_once_with(self.user_2, self.user_2.id)
        mock_create_toast.assert_called_once()

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

    @mock.patch('lobbies.api.controller.handle_lobby_update_ws')
    def test_update_lobby(self, mock_update_ws):
        payload = schemas.LobbyUpdateSchema.from_orm({'mode': Lobby.ModeChoices.CUSTOM})
        lobby = controller.update_lobby(
            self.user_1,
            self.user_1.account.lobby.id,
            payload,
        )
        self.assertEqual(lobby.mode, Lobby.ModeChoices.CUSTOM)
        mock_update_ws.assert_called_once()

        payload = schemas.LobbyUpdateSchema.from_orm({'map_id': 2})
        lobby = controller.update_lobby(
            self.user_1,
            self.user_1.account.lobby.id,
            payload,
        )
        self.assertEqual(lobby.map_id, 2)

        payload = schemas.LobbyUpdateSchema.from_orm(
            {'match_type': Lobby.TypeChoices.SAFEZONE}
        )
        lobby = controller.update_lobby(
            self.user_1,
            self.user_1.account.lobby.id,
            payload,
        )
        self.assertEqual(lobby.match_type, Lobby.TypeChoices.SAFEZONE)

        payload = schemas.LobbyUpdateSchema.from_orm(
            {'weapon': Lobby.WeaponChoices.WEAPON_HEAVYSNIPER}
        )
        lobby = controller.update_lobby(
            self.user_1,
            self.user_1.account.lobby.id,
            payload,
        )
        self.assertEqual(lobby.weapon, Lobby.WeaponChoices.WEAPON_HEAVYSNIPER)

        payload = schemas.LobbyUpdateSchema.from_orm({'queue': 'start'})
        with self.assertRaisesRegex(HttpError, 'in this mode'):
            controller.update_lobby(
                self.user_1,
                self.user_1.account.lobby.id,
                payload,
            )

    def test_update_lobby_queue_maintenence(self):
        AppSettings.objects.filter(name='Maintenance Window').update(value='1')
        payload = schemas.LobbyUpdateSchema.from_orm({'queue': 'start'})
        with self.assertRaisesRegex(HttpError, 'under maintenance'):
            controller.update_lobby(
                self.user_1,
                self.user_1.account.lobby.id,
                payload,
            )

    def test_update_lobby_queue_non_owner(self):
        payload = schemas.LobbyUpdateSchema.from_orm({'queue': 'start'})
        with self.assertRaises(AuthenticationError):
            controller.update_lobby(
                self.user_2,
                self.user_1.account.lobby.id,
                payload,
            )
