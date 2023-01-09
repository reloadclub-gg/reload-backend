from core.tests import APIClient, TestCase
from ..models import Lobby
from . import mixins


class LobbyAPITestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        self.api = APIClient('/api/mm')
        super().setUp()
        self.user_1.auth.add_session()
        self.user_1.auth.create_token()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_3.auth.create_token()
        self.user_2.auth.create_token()

    def test_lobby_leave(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_2.invite(self.user_2.id, self.user_1.id)

        Lobby.move(self.user_1.id, lobby_2.id)

        self.assertEqual(lobby_1.players_count, 0)
        self.assertEqual(lobby_2.players_count, 2)

        response = self.api.call('patch', '/lobby/leave', token=self.user_1.auth.token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_lobby_set_public(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertFalse(lobby.is_public)

        response = self.api.call(
            'patch', '/lobby/set-public', token=self.user_1.auth.token
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(lobby.is_public)

    def test_lobby_set_public_non_owner(self):
        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby.id)

        self.assertFalse(lobby.is_public)

        response = self.api.call(
            'patch', '/lobby/set-public', token=self.user_2.auth.token
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be owner to perfom this action'}
        )

    def test_lobby_set_private(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.set_public()
        self.assertTrue(lobby.is_public)

        response = self.api.call(
            'patch', '/lobby/set-private', token=self.user_1.auth.token
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(lobby.is_public)

    def test_lobby_set_private_non_owner(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.set_public()
        Lobby.create(self.user_2.id)
        Lobby.move(self.user_2.id, lobby.id)

        self.assertTrue(lobby.is_public)

        response = self.api.call(
            'patch', '/lobby/set-private', token=self.user_2.auth.token
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be owner to perfom this action'}
        )

    def test_lobby_remove_player(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(lobby_2.id, self.user_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

        response = self.api.call(
            'patch',
            f'lobby/{lobby_1.id}/remove-player/{self.user_2.id}/',
            token=self.user_1.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_remove_user_outside_lobby(self):
        Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby = Lobby.create(self.user_3.id)

        response = self.api.call(
            'patch',
            f'lobby/{lobby.id}/remove-player/{self.user_2.id}/',
            token=self.user_1.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be in lobby to perform this action'}
        )

    def test_remove_user_by_non_owner(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_3 = Lobby.create(self.user_3.id)

        lobby_1.invite(self.user_1.id, lobby_2.id)
        Lobby.move(lobby_2.id, self.user_1.id)

        lobby_1.invite(self.user_1.id, lobby_3.id)
        Lobby.move(lobby_3.id, self.user_1.id)

        response = self.api.call(
            'patch',
            f'lobby/{lobby_1.id}/remove-player/{self.user_2.id}/',
            token=self.user_3.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be owner to perform this action'}
        )

    def test_lobby_invite(self):
        lobby = Lobby.create(self.user_1.id)

        response = self.api.call(
            'post',
            f'lobby/{lobby.id}/invite-player/{self.user_2.id}/',
            token=self.user_1.auth.token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            self.user_1.account.lobby.invites,
            [f'{self.user_1.id}:{self.user_2.id}'],
        )

    def test_lobby_invite_user_already_been_invited(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, lobby_2.id)

        response = self.api.call(
            'post',
            f'lobby/{lobby_1.id}/invite-player/{lobby_2.id}/',
            token=self.user_1.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User already invited caught on lobby invite'}
        )

    def test_lobby_accept_invite_has_no_invited(self):
        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)

        self.assertListEqual(lobby.invites, [])

        response = self.api.call(
            'patch',
            f'/lobby/{lobby.id}/accept-invite/{self.user_1.id}:{self.user_2.id}/',
            token=self.user_2.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User not invited caught on lobby move'}
        )

    def test_lobby_refuse_invite(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.invite(self.user_1.id, self.user_2.id)

        Lobby.create(self.user_2.id)

        self.assertListEqual(lobby.invites, [f'{self.user_1.id}:{self.user_2.id}'])

        response = self.api.call(
            'patch',
            f'/lobby/{lobby.id}/refuse-invite/{self.user_1.id}:{self.user_2.id}/',
            token=self.user_2.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby.players_count, 1)
        self.assertListEqual(lobby.invites, [])

    def test_lobby_refuse_invite_has_no_invited(self):
        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)

        self.assertListEqual(lobby.invites, [])

        response = self.api.call(
            'patch',
            f'/lobby/{lobby.id}/refuse-invite/{self.user_1.id}:{self.user_2.id}/',
            token=self.user_2.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'Inexistent invite caught on invite deletion'}
        )

    def test_lobby_change_type_and_mode(self):
        lobby = Lobby.create(self.user_1.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        lobby_id = lobby.id
        lobby_type = 'custom'
        lobby_mode = 20

        response = self.api.call(
            'patch',
            f'/lobby/{lobby_id}/change-type/{lobby_type}/change-mode/{lobby_mode}/',
            token=self.user_1.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby.mode, 20)
        self.assertEqual(lobby.lobby_type, 'custom')

    def test_lobby_change_type_and_mode_by_non_owner(self):
        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        lobby_id = lobby.id
        lobby_type = 'custom'
        lobby_mode = 20

        response = self.api.call(
            'patch',
            f'/lobby/{lobby_id}/change-type/{lobby_type}/change-mode/{lobby_mode}/',
            token=self.user_2.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User must be owner to perfom this action'}
        )

    def test_lobby_enter(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_1.set_public()
        lobby_2 = Lobby.create(self.user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        response = self.api.call(
            'patch',
            f'/lobby/{lobby_1.id}/enter/',
            token=self.user_2.auth.token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

    def test_lobby_enter_isnt_public(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        response = self.api.call(
            'patch',
            f'/lobby/{lobby_1.id}/enter/',
            token=self.user_2.auth.token,
        )

        self.assertEqual(response.status_code, 400)
        self.assertDictEqual(
            response.json(), {'detail': 'User not invited caught on lobby move'}
        )
