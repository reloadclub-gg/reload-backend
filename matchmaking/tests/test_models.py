from core.tests import TestCase, cache
from ..models import Lobby
from ..models.lobby import LobbyException
from . import mixins


class LobbyModelTestCase(mixins.SomePlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.online_verified_user_1.auth.add_session()
        self.online_verified_user_2.auth.add_session()
        self.online_verified_user_3.auth.add_session()
        self.online_verified_user_4.auth.add_session()
        self.online_verified_user_5.auth.add_session()
        self.online_verified_user_6.auth.add_session()
        self.online_noaccount_user.auth.add_session()
        self.online_unverified_user.auth.add_session()

    def test_create(self):
        lobby = Lobby(owner_id=self.online_verified_user_1.id)
        cached_lobby = cache.get(lobby.cache_key)
        self.assertIsNone(cached_lobby)

        lobby = Lobby.create(self.online_verified_user_1.id)
        current_lobby_id = cache.get(lobby.cache_key)
        self.assertIsNotNone(current_lobby_id)
        self.assertEqual(
            lobby.cache_key,
            f'{Lobby.Config.CACHE_PREFIX}:{self.online_verified_user_1.id}',
        )
        self.assertEqual(current_lobby_id, str(self.online_verified_user_1.id))
        self.assertEqual(lobby.players_ids, [self.online_verified_user_1.id])
        self.assertEqual(lobby.lobby_type, Lobby.Config.TYPES[0])
        self.assertEqual(
            lobby.mode, Lobby.Config.MODES.get(Lobby.Config.TYPES[0]).get('default')
        )

    def test_create_type(self):
        lobby = Lobby.create(self.online_verified_user_1.id, lobby_type='custom')
        current_lobby_id = cache.get(lobby.cache_key)
        self.assertIsNotNone(current_lobby_id)
        self.assertEqual(lobby.lobby_type, 'custom')

    def test_create_type_unknown(self):
        with self.assertRaisesRegex(LobbyException, 'Type unknown'):
            Lobby.create(self.online_verified_user_1.id, lobby_type='unknown')

    def test_create_mode(self):
        lobby = Lobby.create(self.online_verified_user_1.id, mode=1)
        current_lobby_id = cache.get(lobby.cache_key)
        self.assertIsNotNone(current_lobby_id)
        self.assertEqual(lobby.mode, 1)

    def test_create_mode_and_type(self):
        lobby = Lobby.create(
            self.online_verified_user_1.id, lobby_type='custom', mode=20
        )
        current_lobby_id = cache.get(lobby.cache_key)
        self.assertIsNotNone(current_lobby_id)
        self.assertEqual(lobby.mode, 20)

    def test_create_mode_unknown(self):
        with self.assertRaisesRegex(LobbyException, 'Mode unknown'):
            Lobby.create(self.online_verified_user_1.id, mode=7)

    def test_create_type_and_mode_not_compliant(self):
        with self.assertRaisesRegex(LobbyException, 'Mode unknown'):
            Lobby.create(
                self.online_verified_user_1.id, lobby_type='competitive', mode=20
            )

    def test_create_user_not_found(self):
        with self.assertRaisesRegex(LobbyException, 'not found'):
            Lobby.create(12345)

    def test_create_user_account_unverified(self):
        with self.assertRaisesRegex(LobbyException, 'verified account'):
            Lobby.create(self.online_unverified_user.id)

    def test_create_user_offline(self):
        with self.assertRaisesRegex(LobbyException, 'Offline'):
            Lobby.create(self.offline_verified_user.id)

    def test_invite(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)

        lobby_1.invite(self.online_verified_user_2.id)
        invites = list(map(int, cache.smembers(f'{lobby_1.cache_key}:invites')))
        self.assertEqual(invites, [self.online_verified_user_2.id])
        self.assertEqual(lobby_1.invites, [self.online_verified_user_2.id])

    def test_invite_queue(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)

        lobby_1.start_queue()

        with self.assertRaisesRegex(LobbyException, 'queued'):
            lobby_1.invite(self.online_verified_user_2.id)

    def test_invite_full(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)
        Lobby.create(self.online_verified_user_3.id)
        Lobby.create(self.online_verified_user_4.id)
        Lobby.create(self.online_verified_user_5.id)
        Lobby.create(self.online_verified_user_6.id)

        lobby_1.invite(self.online_verified_user_2.id)
        Lobby.move(self.online_verified_user_2.id, lobby_1.id)
        lobby_1.invite(self.online_verified_user_3.id)
        Lobby.move(self.online_verified_user_3.id, lobby_1.id)
        lobby_1.invite(self.online_verified_user_4.id)
        Lobby.move(self.online_verified_user_4.id, lobby_1.id)
        lobby_1.invite(self.online_verified_user_5.id)
        Lobby.move(self.online_verified_user_5.id, lobby_1.id)

        with self.assertRaisesRegex(LobbyException, 'full'):
            lobby_1.invite(self.online_verified_user_6.id)

    def test_move(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)

        lobby_1.invite(self.online_verified_user_2.id)
        Lobby.move(self.online_verified_user_2.id, lobby_1.id)
        current_moved_player_lobby = cache.get(lobby_2.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_1.id))
        self.assertEqual(len(cache.smembers(f'{lobby_1.cache_key}:invites')), 0)
        self.assertEqual(lobby_2.players_ids, [])
        self.assertCountEqual(
            lobby_1.players_ids,
            [
                self.online_verified_user_1.id,
                self.online_verified_user_2.id,
            ],
        )

    def test_move2(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_3 = Lobby.create(self.online_verified_user_3.id)

        lobby_1.invite(self.online_verified_user_3.id)
        Lobby.move(self.online_verified_user_3.id, lobby_1.id)

        lobby_2.invite(self.online_verified_user_3.id)
        Lobby.move(self.online_verified_user_3.id, lobby_2.id)

        current_moved_player_lobby = cache.get(lobby_3.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_2.id))
        self.assertEqual(len(cache.smembers(f'{lobby_2.cache_key}:invites')), 0)
        self.assertEqual(lobby_3.players_ids, [])
        self.assertEqual(lobby_1.players_ids, [self.online_verified_user_1.id])
        self.assertCountEqual(
            lobby_2.players_ids,
            [
                self.online_verified_user_3.id,
                self.online_verified_user_2.id,
            ],
        )

    def test_move_remaining(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_3 = Lobby.create(self.online_verified_user_3.id)

        lobby_1.invite(self.online_verified_user_3.id)
        Lobby.move(self.online_verified_user_3.id, lobby_1.id)

        lobby_2.invite(self.online_verified_user_1.id)
        Lobby.move(self.online_verified_user_1.id, lobby_2.id)

        current_moved_player_lobby = cache.get(lobby_1.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_2.id))
        self.assertEqual(len(cache.smembers(f'{lobby_2.cache_key}:invites')), 0)
        self.assertEqual(lobby_1.players_ids, [])
        self.assertEqual(lobby_3.players_ids, [self.online_verified_user_3.id])
        self.assertCountEqual(
            lobby_2.players_ids,
            [
                self.online_verified_user_1.id,
                self.online_verified_user_2.id,
            ],
        )

    def test_move_remaining2(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        Lobby.create(self.online_verified_user_3.id)
        Lobby.create(self.online_verified_user_4.id)

        lobby_1.invite(self.online_verified_user_3.id)
        lobby_1.invite(self.online_verified_user_4.id)
        Lobby.move(self.online_verified_user_3.id, lobby_1.id)
        Lobby.move(self.online_verified_user_4.id, lobby_1.id)

        lobby_id_to_receive_remaining_players = min(lobby_1.non_owners_ids)
        new_lobby = Lobby(owner_id=lobby_id_to_receive_remaining_players)

        lobby_2.invite(self.online_verified_user_1.id)
        Lobby.move(self.online_verified_user_1.id, lobby_2.id)

        current_moved_player_lobby = cache.get(lobby_1.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_2.id))
        self.assertEqual(len(cache.smembers(f'{lobby_2.cache_key}:invites')), 0)
        self.assertEqual(lobby_1.players_ids, [])
        self.assertCountEqual(
            new_lobby.players_ids,
            [
                self.online_verified_user_3.id,
                self.online_verified_user_4.id,
            ],
        )
        self.assertCountEqual(
            lobby_2.players_ids,
            [
                self.online_verified_user_1.id,
                self.online_verified_user_2.id,
            ],
        )

    def test_cancel(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)
        Lobby.create(self.online_verified_user_3.id)
        Lobby.create(self.online_verified_user_4.id)

        lobby_1.invite(self.online_verified_user_3.id)
        lobby_1.invite(self.online_verified_user_4.id)
        Lobby.move(self.online_verified_user_3.id, lobby_1.id)
        Lobby.move(self.online_verified_user_4.id, lobby_1.id)

        lobby_id_to_receive_remaining_players = min(lobby_1.non_owners_ids)
        new_lobby = Lobby(owner_id=lobby_id_to_receive_remaining_players)

        Lobby.move(self.online_verified_user_1.id, lobby_1.id)

        self.assertEqual(lobby_1.players_ids, [self.online_verified_user_1.id])
        self.assertCountEqual(
            new_lobby.players_ids,
            [
                self.online_verified_user_3.id,
                self.online_verified_user_4.id,
            ],
        )

    def test_cancel_remove(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        Lobby.create(self.online_verified_user_2.id)
        Lobby.create(self.online_verified_user_3.id)
        Lobby.create(self.online_verified_user_4.id)

        lobby_1.invite(self.online_verified_user_3.id)
        lobby_1.invite(self.online_verified_user_4.id)
        Lobby.move(self.online_verified_user_3.id, lobby_1.id)
        Lobby.move(self.online_verified_user_4.id, lobby_1.id)

        lobby_id_to_receive_remaining_players = min(lobby_1.non_owners_ids)
        new_lobby = Lobby(owner_id=lobby_id_to_receive_remaining_players)

        Lobby.move(self.online_verified_user_1.id, lobby_1.id, remove=True)

        self.assertEqual(
            cache.exists(
                lobby_1.cache_key,
                f'{lobby_1.cache_key}:players',
                f'{lobby_1.cache_key}:queue',
                f'{lobby_1.cache_key}:is_public',
                f'{lobby_1.cache_key}:invites',
            ),
            0,
        )
        self.assertCountEqual(
            new_lobby.players_ids,
            [
                self.online_verified_user_3.id,
                self.online_verified_user_4.id,
            ],
        )

    def test_lobby_set_public(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_1.set_public()
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_1.move(lobby_2.id, self.online_verified_user_1.id)

        self.assertTrue(lobby_1.is_public)
        self.assertEqual(lobby_1.players_count, 2)

    def test_lobby_set_private(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_1.set_public()
        self.assertTrue(lobby_1.is_public)
        lobby_1.set_private()
        self.assertFalse(lobby_1.is_public)

        lobby_2 = Lobby.create(self.online_verified_user_2.id)

        with self.assertRaisesMessage(
            LobbyException, 'User not invited caught on lobby move'
        ):
            lobby_1.move(lobby_2.id, self.online_verified_user_1.id)

    def test_max_players(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        self.assertEqual(
            lobby.max_players, Lobby.Config.MODES.get(lobby.lobby_type).get('default')
        )

        lobby = Lobby.create(self.online_verified_user_1.id, lobby_type='custom')
        self.assertEqual(
            lobby.max_players, Lobby.Config.MODES.get(lobby.lobby_type).get('default')
        )

        lobby = Lobby.create(
            self.online_verified_user_1.id, lobby_type='competitive', mode=1
        )
        self.assertEqual(lobby.max_players, 1)

    def test_set_type(self):
        lobby = Lobby.create(self.online_verified_user_1.id, lobby_type='custom')
        self.assertEqual(lobby.lobby_type, 'custom')
        lobby.set_type('competitive')
        self.assertEqual(lobby.lobby_type, 'competitive')

    def test_set_type_unknown(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        self.assertEqual(lobby.lobby_type, lobby.Config.TYPES[0])

        with self.assertRaisesRegex(LobbyException, 'Type unknown'):
            lobby.set_type('unknown')

        self.assertEqual(lobby.lobby_type, lobby.Config.TYPES[0])

    def test_set_mode(self):
        lobby = Lobby.create(self.online_verified_user_1.id, mode=1)
        self.assertEqual(lobby.mode, 1)

        lobby.set_mode(5)
        self.assertEqual(lobby.mode, 5)

    def test_set_mode_unknown(self):
        lobby = Lobby.create(self.online_verified_user_1.id, mode=1)
        self.assertEqual(lobby.mode, 1)

        with self.assertRaisesRegex(LobbyException, 'Mode unknown'):
            lobby.set_mode(20)

        self.assertEqual(lobby.mode, 1)

    def test_delete_invite(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_1.invite(lobby_2.id)

        self.assertListEqual(lobby_1.invites, [lobby_2.id])

        lobby_1.delete_invite(lobby_2.id)

        self.assertListEqual(lobby_1.invites, [])

    def test_delete_invite_must_be_invited(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)

        self.assertFalse(lobby_1.delete_invite(lobby_2.id))
