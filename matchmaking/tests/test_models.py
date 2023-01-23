from time import sleep
from unittest import mock

from core.tests import TestCase, cache

from ..models import (
    Lobby,
    LobbyException,
    LobbyInvite,
    LobbyInviteException,
    Team,
    TeamException,
)
from . import mixins


class LobbyModelTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()
        self.online_noaccount_user.auth.add_session()
        self.online_unverified_user.auth.add_session()

    def test_create(self):
        lobby = Lobby(owner_id=self.user_1.id)
        cached_lobby = cache.get(lobby.cache_key)
        self.assertIsNone(cached_lobby)

        lobby = Lobby.create(self.user_1.id)
        current_lobby_id = cache.get(lobby.cache_key)
        self.assertIsNotNone(current_lobby_id)
        self.assertEqual(
            lobby.cache_key,
            f'{Lobby.Config.CACHE_PREFIX}:{self.user_1.id}',
        )
        self.assertEqual(current_lobby_id, str(self.user_1.id))
        self.assertEqual(lobby.players_ids, [self.user_1.id])
        self.assertEqual(lobby.lobby_type, Lobby.Config.TYPES[0])
        self.assertEqual(
            lobby.mode, Lobby.Config.MODES.get(Lobby.Config.TYPES[0]).get('default')
        )

    def test_create_type(self):
        lobby = Lobby.create(self.user_1.id, lobby_type='custom')
        current_lobby_id = cache.get(lobby.cache_key)
        self.assertIsNotNone(current_lobby_id)
        self.assertEqual(lobby.lobby_type, 'custom')

    def test_create_type_unknown(self):
        with self.assertRaises(LobbyException):
            Lobby.create(self.user_1.id, lobby_type='unknown')

    def test_create_mode(self):
        lobby = Lobby.create(self.user_1.id, mode=1)
        current_lobby_id = cache.get(lobby.cache_key)
        self.assertIsNotNone(current_lobby_id)
        self.assertEqual(lobby.mode, 1)

    def test_create_mode_and_type(self):
        lobby = Lobby.create(self.user_1.id, lobby_type='custom', mode=20)
        current_lobby_id = cache.get(lobby.cache_key)
        self.assertIsNotNone(current_lobby_id)
        self.assertEqual(lobby.mode, 20)

    def test_create_mode_unknown(self):
        with self.assertRaises(LobbyException):
            Lobby.create(self.user_1.id, mode=7)

    def test_create_type_and_mode_not_compliant(self):
        with self.assertRaises(LobbyException):
            Lobby.create(self.user_1.id, lobby_type='competitive', mode=20)

    def test_create_user_not_found(self):
        with self.assertRaises(LobbyException):
            Lobby.create(12345)

    def test_create_user_account_unverified(self):
        with self.assertRaises(LobbyException):
            Lobby.create(self.online_unverified_user.id)

    def test_create_user_offline(self):
        with self.assertRaises(LobbyException):
            Lobby.create(self.offline_verified_user.id)

    def test_invite(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        invites = list(cache.smembers(f'{lobby_1.cache_key}:invites'))
        self.assertEqual(invites, [f'{self.user_1.id}:{self.user_2.id}'])
        self.assertEqual(lobby_1.invites, [f'{self.user_1.id}:{self.user_2.id}'])

    def test_invite_queue(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)

        lobby_1.start_queue()

        with self.assertRaises(LobbyException):
            lobby_1.invite(self.user_1.id, self.user_2.id)

    def test_invite_full(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)
        Lobby.create(self.user_6.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_3.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        Lobby.move(self.user_4.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_5.id)
        Lobby.move(self.user_5.id, lobby_1.id)

        with self.assertRaises(LobbyException):
            lobby_1.invite(self.user_1.id, self.user_6.id)

    def test_move(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        current_moved_player_lobby = cache.get(lobby_2.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_1.id))
        self.assertEqual(len(cache.smembers(f'{lobby_1.cache_key}:invites')), 0)
        self.assertEqual(lobby_2.players_ids, [])
        self.assertCountEqual(
            lobby_1.players_ids,
            [
                self.user_1.id,
                self.user_2.id,
            ],
        )

    def test_move2(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_3 = Lobby.create(self.user_3.id)

        lobby_1.invite(self.user_1.id, self.user_3.id)
        Lobby.move(self.user_3.id, lobby_1.id)

        lobby_2.invite(self.user_2.id, self.user_3.id)
        Lobby.move(self.user_3.id, lobby_2.id)

        current_moved_player_lobby = cache.get(lobby_3.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_2.id))
        self.assertEqual(len(cache.smembers(f'{lobby_2.cache_key}:invites')), 0)
        self.assertEqual(lobby_3.players_ids, [])
        self.assertEqual(lobby_1.players_ids, [self.user_1.id])
        self.assertCountEqual(
            lobby_2.players_ids,
            [
                self.user_3.id,
                self.user_2.id,
            ],
        )

    def test_move_remaining(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_3 = Lobby.create(self.user_3.id)

        lobby_1.invite(self.user_1.id, self.user_3.id)
        Lobby.move(self.user_3.id, lobby_1.id)

        lobby_2.invite(self.user_2.id, self.user_1.id)
        Lobby.move(self.user_1.id, lobby_2.id)

        current_moved_player_lobby = cache.get(lobby_1.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_2.id))
        self.assertEqual(len(cache.smembers(f'{lobby_2.cache_key}:invites')), 0)
        self.assertEqual(lobby_1.players_ids, [])
        self.assertEqual(lobby_3.players_ids, [self.user_3.id])
        self.assertCountEqual(
            lobby_2.players_ids,
            [
                self.user_1.id,
                self.user_2.id,
            ],
        )

    def test_move_remaining2(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)

        lobby_1.invite(self.user_1.id, self.user_3.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        Lobby.move(self.user_4.id, lobby_1.id)

        lobby_id_to_receive_remaining_players = min(lobby_1.non_owners_ids)
        new_lobby = Lobby(owner_id=lobby_id_to_receive_remaining_players)

        lobby_2.invite(self.user_2.id, self.user_1.id)
        Lobby.move(self.user_1.id, lobby_2.id)

        current_moved_player_lobby = cache.get(lobby_1.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_2.id))
        self.assertEqual(len(cache.smembers(f'{lobby_2.cache_key}:invites')), 0)
        self.assertEqual(lobby_1.players_ids, [])
        self.assertCountEqual(
            new_lobby.players_ids,
            [
                self.user_3.id,
                self.user_4.id,
            ],
        )
        self.assertCountEqual(
            lobby_2.players_ids,
            [
                self.user_1.id,
                self.user_2.id,
            ],
        )

    def test_cancel(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)

        lobby_1.invite(self.user_1.id, self.user_3.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        Lobby.move(self.user_4.id, lobby_1.id)

        lobby_id_to_receive_remaining_players = min(lobby_1.non_owners_ids)
        new_lobby = Lobby(owner_id=lobby_id_to_receive_remaining_players)

        Lobby.move(self.user_1.id, lobby_1.id)

        self.assertEqual(lobby_1.players_ids, [self.user_1.id])
        self.assertCountEqual(
            new_lobby.players_ids,
            [
                self.user_3.id,
                self.user_4.id,
            ],
        )

    def test_cancel_remove(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)

        lobby_1.invite(self.user_1.id, self.user_3.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        Lobby.move(self.user_4.id, lobby_1.id)

        lobby_id_to_receive_remaining_players = min(lobby_1.non_owners_ids)
        new_lobby = Lobby(owner_id=lobby_id_to_receive_remaining_players)

        Lobby.move(self.user_1.id, lobby_1.id, remove=True)

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
                self.user_3.id,
                self.user_4.id,
            ],
        )

    def test_lobby_set_public(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_1.set_public()
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_1.move(lobby_2.id, self.user_1.id)

        self.assertTrue(lobby_1.is_public)
        self.assertEqual(lobby_1.players_count, 2)

    def test_lobby_set_private(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_1.set_public()
        self.assertTrue(lobby_1.is_public)
        lobby_1.set_private()
        self.assertFalse(lobby_1.is_public)

        lobby_2 = Lobby.create(self.user_2.id)

        with self.assertRaises(LobbyException):
            lobby_1.move(lobby_2.id, self.user_1.id)

    def test_max_players(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertEqual(
            lobby.max_players, Lobby.Config.MODES.get(lobby.lobby_type).get('default')
        )

        lobby = Lobby.create(self.user_1.id, lobby_type='custom')
        self.assertEqual(
            lobby.max_players, Lobby.Config.MODES.get(lobby.lobby_type).get('default')
        )

        lobby = Lobby.create(self.user_1.id, lobby_type='competitive', mode=1)
        self.assertEqual(lobby.max_players, 1)

    def test_set_type(self):
        lobby = Lobby.create(self.user_1.id, lobby_type='custom')
        self.assertEqual(lobby.lobby_type, 'custom')
        lobby.set_type('competitive')
        self.assertEqual(lobby.lobby_type, 'competitive')

    def test_set_type_unknown(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertEqual(lobby.lobby_type, lobby.Config.TYPES[0])

        with self.assertRaises(LobbyException):
            lobby.set_type('unknown')

        self.assertEqual(lobby.lobby_type, lobby.Config.TYPES[0])

    def test_set_mode(self):
        lobby = Lobby.create(self.user_1.id, mode=1)
        self.assertEqual(lobby.mode, 1)

        lobby.set_mode(5)
        self.assertEqual(lobby.mode, 5)

    def test_set_mode_unknown(self):
        lobby = Lobby.create(self.user_1.id, mode=1)
        self.assertEqual(lobby.mode, 1)

        with self.assertRaises(LobbyException):
            lobby.set_mode(20)

        self.assertEqual(lobby.mode, 1)

    def test_delete_invite(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, lobby_2.id)
        self.assertListEqual(lobby_1.invites, [f'{self.user_1.id}:{self.user_2.id}'])

        lobby_1.delete_invite(f'{self.user_1.id}:{self.user_2.id}')
        self.assertListEqual(lobby_1.invites, [])

    def test_delete_invite_must_be_invited(self):
        lobby_1 = Lobby.create(self.user_1.id)

        with self.assertRaises(LobbyException):
            lobby_1.delete_invite(f'{self.user_1.id}:{self.user_2.id}')

    def test_set_mode_20x20_to_5x5(self):
        lobby_1 = Lobby.create(
            self.user_1.id, lobby_type=Lobby.Config.TYPES[1], mode=20
        )

        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)
        Lobby.create(self.user_6.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_3.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        Lobby.move(self.user_4.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_5.id)
        Lobby.move(self.user_5.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_6.id)
        Lobby.move(self.user_6.id, lobby_1.id)

        self.assertEqual(lobby_1.mode, 20)
        self.assertEqual(lobby_1.players_count, 6)

        lobby_1.set_type('competitive')
        lobby_1.set_mode(5)

        self.assertEqual(lobby_1.mode, 5)
        self.assertEqual(lobby_1.players_count, 5)

    def test_set_mode_5x5_to_1x1(self):
        lobby_1 = Lobby.create(self.user_1.id, lobby_type=Lobby.Config.TYPES[0], mode=5)

        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_3.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        Lobby.move(self.user_4.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_5.id)
        Lobby.move(self.user_5.id, lobby_1.id)

        self.assertEqual(lobby_1.mode, 5)
        self.assertEqual(lobby_1.players_count, 5)

        lobby_1.set_mode(1)

        self.assertEqual(lobby_1.mode, 1)
        self.assertEqual(lobby_1.players_count, 1)

    def test_set_mode_players_id_to_remove(self):
        lobby_1 = Lobby.create(
            self.user_1.id, lobby_type=Lobby.Config.TYPES[1], mode=20
        )

        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)
        Lobby.create(self.user_6.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_3.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        Lobby.move(self.user_4.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_5.id)
        Lobby.move(self.user_5.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_6.id)
        Lobby.move(self.user_6.id, lobby_1.id)

        self.assertEqual(lobby_1.mode, 20)
        self.assertEqual(lobby_1.players_count, 6)
        self.assertListEqual(
            sorted(lobby_1.players_ids),
            [
                self.user_1.id,
                self.user_2.id,
                self.user_3.id,
                self.user_4.id,
                self.user_5.id,
                self.user_6.id,
            ],
        )

        lobby_1.set_type('competitive')
        lobby_1.set_mode(5, [self.user_4.id])

        self.assertEqual(lobby_1.mode, 5)
        self.assertEqual(lobby_1.players_count, 5)
        self.assertListEqual(
            sorted(lobby_1.players_ids),
            [
                self.user_1.id,
                self.user_2.id,
                self.user_3.id,
                self.user_5.id,
                self.user_6.id,
            ],
        )
        self.assertEqual(self.user_4.account.lobby.id, self.user_4.id)

    def test_set_mode_players_id_to_remove_with_owner_id(self):
        lobby_1 = Lobby.create(
            self.user_1.id, lobby_type=Lobby.Config.TYPES[1], mode=20
        )

        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)
        Lobby.create(self.user_6.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_3.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        Lobby.move(self.user_4.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_5.id)
        Lobby.move(self.user_5.id, lobby_1.id)
        lobby_1.invite(self.user_1.id, self.user_6.id)
        Lobby.move(self.user_6.id, lobby_1.id)

        self.assertEqual(lobby_1.mode, 20)
        self.assertEqual(lobby_1.players_count, 6)
        self.assertListEqual(
            sorted(lobby_1.players_ids),
            [
                self.user_1.id,
                self.user_2.id,
                self.user_3.id,
                self.user_4.id,
                self.user_5.id,
                self.user_6.id,
            ],
        )

        lobby_1.set_type('competitive')
        with self.assertRaises(LobbyException):
            lobby_1.set_mode(5, [self.user_1.id])

    def test_move_delete_invites_from_player(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        lobby_1.invite(self.user_2.id, self.user_3.id)

        self.assertEqual(
            lobby_1.get_invites_by_from_player_id(self.user_2.id),
            [f'{self.user_2.id}:{self.user_3.id}'],
        )

        Lobby.move(self.user_2.id, self.user_2.id)

        self.assertEqual(
            lobby_1.get_invites_by_from_player_id(self.user_2.id),
            [],
        )

    def test_queueing_should_delete_all_invites(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        lobby_1.invite(self.user_2.id, self.user_3.id)

        self.assertEqual(
            lobby_1.get_invites_by_from_player_id(self.user_2.id),
            [f'{self.user_2.id}:{self.user_3.id}'],
        )

        lobby_1.start_queue()

        self.assertEqual(
            lobby_1.get_invites_by_from_player_id(self.user_2.id),
            [],
        )

    def test_get_lobby_invite(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        invite_expected = lobby_1.invite(self.user_1.id, self.user_2.id)

        self.assertEqual(
            invite_expected,
            LobbyInvite.get(lobby_1.id, f'{self.user_1.id}:{self.user_2.id}'),
        )

    def test_get_lobby_invite_with_raise(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)

        with self.assertRaises(LobbyInviteException):
            LobbyInvite.get(lobby_1.id, '99:99')

    def test_overall(self):
        self.user_1.account.level = 1
        self.user_1.account.save()
        self.user_2.account.level = 2
        self.user_2.account.save()
        self.user_3.account.level = 3
        self.user_3.account.save()
        self.user_4.account.level = 4
        self.user_4.account.save()
        self.user_5.account.level = 5
        self.user_5.account.save()

        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_3 = Lobby.create(self.user_3.id)
        lobby_4 = Lobby.create(self.user_4.id)
        lobby_5 = Lobby.create(self.user_5.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_3.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        lobby_1.invite(self.user_1.id, self.user_5.id)

        Lobby.move(lobby_2.id, lobby_1.id)
        Lobby.move(lobby_3.id, lobby_1.id)
        Lobby.move(lobby_4.id, lobby_1.id)
        Lobby.move(lobby_5.id, lobby_1.id)

        self.assertEqual(lobby_1.overall, 5)

    def test_queue_time(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.start_queue()
        sleep(2)

        self.assertEqual(lobby.queue_time, 2)

    @mock.patch(
        'matchmaking.models.lobby.Lobby.queue_time', new_callable=mock.PropertyMock
    )
    def test_lobby_overall_by_elapsed_time(self, mocker):
        lobby = Lobby.create(self.user_1.id)
        lobby.start_queue()

        mocker.return_value = 10
        min_level, max_level = lobby.get_overall_by_elapsed_time()
        self.assertEqual((0, 1), (min_level, max_level))

        mocker.return_value = 30
        min_level, max_level = lobby.get_overall_by_elapsed_time()
        self.assertEqual((0, 2), (min_level, max_level))

        mocker.return_value = 60
        min_level, max_level = lobby.get_overall_by_elapsed_time()
        self.assertEqual((0, 3), (min_level, max_level))

        mocker.return_value = 90
        min_level, max_level = lobby.get_overall_by_elapsed_time()
        self.assertEqual((0, 4), (min_level, max_level))

        mocker.return_value = 120
        min_level, max_level = lobby.get_overall_by_elapsed_time()
        self.assertEqual((0, 5), (min_level, max_level))


class TeamModelTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()

        self.lobby1 = Lobby.create(owner_id=self.user_1.id)
        self.lobby2 = Lobby.create(owner_id=self.user_2.id)
        self.lobby3 = Lobby.create(owner_id=self.user_3.id)
        self.lobby4 = Lobby.create(owner_id=self.user_4.id)
        self.lobby5 = Lobby.create(owner_id=self.user_5.id)
        self.lobby6 = Lobby.create(owner_id=self.user_6.id)

    def test_players_count(self):
        team = Team(lobbies_ids=[self.lobby1.id, self.lobby2.id])
        self.assertEqual(
            team.players_count, self.lobby1.players_count + self.lobby2.players_count
        )

    def test_build(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()
        self.lobby5.start_queue()
        self.lobby6.start_queue()

        team = Team.build(self.lobby1)
        team = Team.build(self.lobby1)
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)
        self.assertEqual(team.players_count, self.lobby1.max_players)

    def test_build_skips(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)

        self.lobby4.set_public()
        Lobby.move(self.user_5.id, self.lobby4.id)
        Lobby.move(self.user_6.id, self.lobby4.id)

        self.lobby1.start_queue()
        self.lobby4.start_queue()

        team = Team.build(self.lobby1)
        with self.assertRaises(TeamException):
            Team.get_by_id(team.id)

        team.delete()

        self.lobby4.cancel_queue()

        self.lobby6.cancel_queue()
        Lobby.move(self.user_6.id, self.lobby6.id)
        self.lobby6.start_queue()

        self.lobby4.set_mode(1)
        self.lobby4.start_queue()

        team = Team.build(self.lobby1)
        self.assertEqual(team.lobbies_ids, [self.lobby1.id, self.lobby6.id])
        self.assertEqual(team.players_count, 4)

        team.delete()
        self.user_6.account.level = 7
        self.user_6.account.save()

        team = Team.build(self.lobby1)
        self.assertEqual(team.lobbies_ids, [self.lobby1.id])
        self.assertEqual(team.players_count, 3)

    def test_ready(self):
        team = Team(lobbies_ids=[self.lobby1.id]).save()
        self.assertFalse(team.ready)
        team.set_ready()
        self.assertTrue(team.ready)
        team.set_not_ready()
        self.assertFalse(team.ready)

    def test_build_errors(self):
        Team(lobbies_ids=[self.lobby1.id]).save()
        Team(lobbies_ids=[self.lobby2.id, self.lobby4.id]).save()

        with self.assertRaises(TeamException):
            Team.build(self.lobby1)

        with self.assertRaises(TeamException):
            Team.build(self.lobby2)

        with self.assertRaises(TeamException):
            Team.build(self.lobby4)

        Team.build(self.lobby3)

    def test_get_all(self):
        team1 = Team(lobbies_ids=[self.lobby1.id]).save()
        team2 = Team(lobbies_ids=[self.lobby2.id]).save()
        team3 = Team(
            lobbies_ids=[self.lobby3.id, self.lobby4.id, self.lobby5.id, self.lobby6.id]
        ).save()

        teams = Team.get_all()
        self.assertCountEqual(teams, [team1, team2, team3])
