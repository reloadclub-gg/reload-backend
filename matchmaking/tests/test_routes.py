from core.tests import APIClient, TestCase
from ..models import Lobby
from . import mixins


class LobbyAPITestCase(mixins.SomePlayersMixin, TestCase):
    def setUp(self) -> None:
        self.api = APIClient('/api/mm')
        super().setUp()
        self.online_verified_user_1.auth.add_session()
        self.online_verified_user_1.auth.create_token()
        self.online_verified_user_2.auth.add_session()
        self.online_verified_user_3.auth.add_session()
        self.online_verified_user_3.auth.create_token()
        self.online_verified_user_2.auth.create_token()

    def test_lobby_leave(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_2.invite(self.online_verified_user_1.id)

        Lobby.move(self.online_verified_user_1.id, lobby_2.id)

        self.assertEqual(lobby_1.players_count, 0)
        self.assertEqual(lobby_2.players_count, 2)

        response = self.api.call(
            'patch', '/lobby/leave', token=self.online_verified_user_1.auth.token
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_lobby_set_public(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        self.assertFalse(lobby.is_public)

        response = self.api.call(
            'patch', '/lobby/set-public', token=self.online_verified_user_1.auth.token
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(lobby.is_public)

    def test_lobby_set_private(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        lobby.set_public()
        self.assertTrue(lobby.is_public)

        response = self.api.call(
            'patch', '/lobby/set-private', token=self.online_verified_user_1.auth.token
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(lobby.is_public)

    def test_lobby_remove(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_1.invite(lobby_2.id)
        Lobby.move(lobby_2.id, self.online_verified_user_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

        response = self.api.call(
            'patch',
            f'lobby/{lobby_1.id}/remove-player/{self.online_verified_user_2.id}/',
            token=self.online_verified_user_1.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_remove_user_outside_lobby(self):
        Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)
        lobby = Lobby.create(self.online_verified_user_3.id)

        response = self.api.call(
            'patch',
            f'lobby/{lobby.id}/remove-player/{self.online_verified_user_2.id}/',
            token=self.online_verified_user_1.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be in lobby to perform this action'}
        )

    def test_remove_user_by_non_owner(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_3 = Lobby.create(self.online_verified_user_3.id)

        lobby_1.invite(lobby_2.id)
        Lobby.move(lobby_2.id, self.online_verified_user_1.id)

        lobby_1.invite(lobby_3.id)
        Lobby.move(lobby_3.id, self.online_verified_user_1.id)

        response = self.api.call(
            'patch',
            f'lobby/{lobby_1.id}/remove-player/{self.online_verified_user_2.id}/',
            token=self.online_verified_user_3.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be owner to perform this action'}
        )

    def test_lobby_invite(self):
        lobby = Lobby.create(self.online_verified_user_1.id)

        response = self.api.call(
            'post',
            f'lobby/{lobby.id}/invite-player/{self.online_verified_user_2.id}/',
            token=self.online_verified_user_1.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.online_verified_user_1.account.lobby.invites,
            [self.online_verified_user_2.id],
        )

    def test_lobby_invite_user_by_non_owner(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)

        response = self.api.call(
            'post',
            f'lobby/{lobby_2.id}/invite-player/{lobby_1.id}/',
            token=self.online_verified_user_1.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be owner to perfom this action'}
        )

    def test_lobby_invite_user_already_been_invited(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_1.invite(lobby_2.id)

        response = self.api.call(
            'post',
            f'lobby/{lobby_1.id}/invite-player/{lobby_2.id}/',
            token=self.online_verified_user_1.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'Player id has already been invited'}
        )

    def test_lobby_invite_user_already_in_lobby(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_1.invite(lobby_2.id)
        lobby_1.move(lobby_2.id, lobby_1.id)

        response = self.api.call(
            'post',
            f'lobby/{lobby_1.id}/invite-player/{lobby_2.id}/',
            token=self.online_verified_user_1.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(response.json(), {'detail': 'User already in lobby'})

    def test_lobby_accept_invite(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        lobby.invite(self.online_verified_user_2.id)

        Lobby.create(self.online_verified_user_2.id)

        self.assertListEqual(lobby.invites, [self.online_verified_user_2.id])

        response = self.api.call(
            'patch',
            f'/lobby/{lobby.id}/accept-invite/',
            token=self.online_verified_user_2.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby.players_count, 2)
        self.assertListEqual(lobby.invites, [])

    def test_lobby_accept_invite_has_no_invited(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)

        self.assertListEqual(lobby.invites, [])

        response = self.api.call(
            'patch',
            f'/lobby/{lobby.id}/accept-invite/',
            token=self.online_verified_user_2.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'Player id has not been invited'}
        )

    def test_lobby_refuse_invite(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        lobby.invite(self.online_verified_user_2.id)

        Lobby.create(self.online_verified_user_2.id)

        self.assertListEqual(lobby.invites, [self.online_verified_user_2.id])

        response = self.api.call(
            'patch',
            f'/lobby/{lobby.id}/refuse-invite/',
            token=self.online_verified_user_2.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby.players_count, 1)
        self.assertListEqual(lobby.invites, [])

    def test_lobby_refuse_invite_has_no_invited(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)

        self.assertListEqual(lobby.invites, [])

        response = self.api.call(
            'patch',
            f'/lobby/{lobby.id}/refuse-invite/',
            token=self.online_verified_user_2.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'Player id has not been invited'}
        )

    def test_lobby_change_type_and_mode(self):
        lobby = Lobby.create(self.online_verified_user_1.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        lobby_id = lobby.id
        lobby_type = 'custom'
        lobby_mode = 20

        response = self.api.call(
            'patch',
            f'/lobby/{lobby_id}/change-type/{lobby_type}/change-mode/{lobby_mode}/',
            token=self.online_verified_user_1.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby.mode, 20)
        self.assertEqual(lobby.lobby_type, 'custom')

    def test_lobby_change_type_and_mode_by_non_owner(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        lobby_id = lobby.id
        lobby_type = 'custom'
        lobby_mode = 20

        response = self.api.call(
            'patch',
            f'/lobby/{lobby_id}/change-type/{lobby_type}/change-mode/{lobby_mode}/',
            token=self.online_verified_user_2.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be owner to perfom this action'}
        )
