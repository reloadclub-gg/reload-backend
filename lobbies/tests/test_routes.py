from unittest import mock

from core.tests import APIClient, TestCase
from matchmaking.tests.mixins import VerifiedPlayersMixin

from ..models import Lobby, LobbyInvite


class LobbyRoutesTestCase(VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.api = APIClient('/api/lobbies')
        self.user_1.auth.add_session()
        self.user_1.auth.create_token()
        self.user_2.auth.add_session()
        self.user_2.auth.create_token()
        self.user_3.auth.add_session()
        self.user_3.auth.create_token()

    def test_invites_list(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_3 = Lobby.create(self.user_3.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        lobby_3.invite(self.user_3.id, self.user_2.id)

        response = self.api.call('get', '/invites', token=self.user_2.auth.token)
        self.assertEqual(len(response.json()), 2)

    def test_invite_detail(self):
        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        invite = lobby.invite(self.user_1.id, self.user_2.id)

        response = self.api.call(
            'get',
            f'/invites/{invite.id}/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.json().get('id'), invite.id)

        response = self.api.call(
            'get',
            '/invites/some_id:other_id/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.status_code, 422)

        response = self.api.call(
            'get',
            f'/invites/{invite.id}/',
            token=self.user_3.auth.token,
        )
        self.assertEqual(response.status_code, 401)
        response = self.api.call(
            'get',
            f'/invites/{self.user_1.id}:389756895367/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.status_code, 404)

    @mock.patch('lobbies.api.routes.controller.accept_invite')
    @mock.patch('lobbies.api.routes.controller.refuse_invite')
    def test_invite_delete(self, refuse_mock, accept_mock):
        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        invite = lobby.invite(self.user_1.id, self.user_2.id)
        refuse_mock.return_value = invite
        accept_mock.return_value = invite

        response = self.api.call(
            'delete',
            f'/invites/{invite.id}/',
            token=self.user_2.auth.token,
            data={'refuse': True},
        )
        self.assertEqual(response.status_code, 200)
        refuse_mock.assert_called_once()

        response = self.api.call(
            'delete',
            f'/invites/{invite.id}/',
            token=self.user_2.auth.token,
            data={'accept': True},
        )
        self.assertEqual(response.status_code, 200)
        accept_mock.assert_called_once()

        response = self.api.call(
            'delete',
            f'/invites/{invite.id}/',
            token=self.user_2.auth.token,
            data={'accept': True},
        )
        self.assertEqual(response.status_code, 200)
        refuse_mock.assert_called_once()

        response = self.api.call(
            'delete',
            f'/invites/{invite.id}/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.status_code, 400)

    def test_invite_create(self):
        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)

        response = self.api.call(
            'post',
            f'/invites/',
            token=self.user_2.auth.token,
            data={
                'lobby_id': lobby.id,
                'from_user_id': self.user_1.id,
                'to_user_id': self.user_2.id,
            },
        )
        self.assertEqual(response.status_code, 200)

        invite = LobbyInvite.get_by_id(response.json().get('id'))
        self.assertIsNotNone(invite)
        self.assertEqual(invite.id, response.json().get('id'))

    def test_invite_delete_auth_error(self):
        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        invite = lobby.invite(self.user_1.id, self.user_2.id)
        response = self.api.call(
            'delete',
            f'/invites/{invite.id}/',
            token=self.user_1.auth.token,
            data={'refuse': True},
        )
        self.assertEqual(response.status_code, 401)

    def test_player_delete(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)

        response = self.api.call(
            'delete',
            f'/{lobby_1.id}/players/{self.user_2.id}/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.json().get('players_count'), 1)

    def test_player_delete_not_authorized(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)

        response = self.api.call(
            'delete',
            f'/{lobby_1.id}/players/{self.user_1.id}/',
            token=self.user_2.auth.token,
        )
        self.assertEqual(response.status_code, 401)

    def test_lobby_update(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        self.assertIsNone(lobby_1.queue)

        response = self.api.call(
            'patch',
            f'/{lobby_1.id}',
            token=self.user_1.auth.token,
            data={'start_queue': True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(lobby_1.queue)

    def test_lobby_update_not_authorized(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        self.assertIsNone(lobby_1.queue)

        response = self.api.call(
            'patch',
            f'/{lobby_1.id}',
            token=self.user_2.auth.token,
            data={'start_queue': True},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIsNone(lobby_1.queue)

    def test_lobby_update_error(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        self.assertIsNone(lobby_1.queue)

        response = self.api.call(
            'patch',
            f'/{lobby_1.id}',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(lobby_1.queue)

    def test_detail(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        response = self.api.call('get', f'/{lobby_1.id}', token=self.user_1.auth.token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('id'), lobby_1.id)

        response = self.api.call('get', f'/{lobby_1.id}', token=self.user_2.auth.token)
        self.assertEqual(response.status_code, 401)
