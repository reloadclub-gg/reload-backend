import datetime
import time
from time import sleep
from unittest import mock

from django.conf import settings
from django.utils import timezone

from accounts.models import User
from core.redis import RedisClient
from core.tests import TestCase, cache
from core.utils import generate_random_string, str_to_timezone

from ..models import (
    Lobby,
    LobbyException,
    LobbyInvite,
    LobbyInviteException,
    Player,
    PlayerException,
    PreMatch,
    PreMatchConfig,
    PreMatchException,
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
        self.assertEqual(
            lobby_1.invites,
            [
                LobbyInvite(
                    lobby_id=lobby_1.id, from_id=self.user_1.id, to_id=self.user_2.id
                )
            ],
        )

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
        new_lobby = Lobby.move(self.user_3.id, lobby_1.id)
        self.assertIsNone(new_lobby)

        lobby_2.invite(self.user_2.id, self.user_1.id)
        new_lobby = Lobby.move(self.user_1.id, lobby_2.id)
        self.assertIsNotNone(new_lobby)

        current_moved_player_lobby = cache.get(lobby_1.cache_key)
        self.assertEqual(current_moved_player_lobby, str(lobby_2.id))
        self.assertEqual(len(cache.smembers(f'{lobby_2.cache_key}:invites')), 0)
        self.assertEqual(lobby_1.players_ids, [])
        self.assertEqual(new_lobby.id, lobby_3.id)
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

    def test_move_remove(self):
        lobby = Lobby.create(self.user_1.id)
        Lobby.move(self.user_1.id, lobby.id, remove=True)
        self.assertEqual(len(cache.keys(f'{Lobby.Config.CACHE_PREFIX}:{lobby.id}*')), 0)

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

    def test_lobby_move_on_queue(self):
        lobby1 = Lobby.create(self.user_1.id)
        lobby2 = Lobby.create(self.user_2.id)
        lobby1.set_public()
        Lobby.move(self.user_2.id, lobby1.id)
        lobby1.start_queue()

        with self.assertRaises(LobbyException):
            Lobby.move(self.user_2.id, lobby2.id)

        Lobby.move(self.user_2.id, lobby2.id, remove=True)
        self.assertIsNone(lobby1.queue)
        self.assertIsNone(lobby1.queue_time)
        self.assertCountEqual(lobby1.players_ids, [self.user_1.id])

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
        self.assertListEqual(
            lobby_1.invites,
            [
                LobbyInvite(
                    lobby_id=lobby_1.id, from_id=self.user_1.id, to_id=self.user_2.id
                )
            ],
        )

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
            [
                LobbyInvite(
                    from_id=self.user_2.id,
                    to_id=self.user_3.id,
                    lobby_id=lobby_1.id,
                )
            ],
        )

        Lobby.move(self.user_2.id, self.user_2.id)

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
        min_level, max_level = lobby.get_min_max_overall_by_queue_time()
        self.assertEqual((0, 1), (min_level, max_level))

        mocker.return_value = 30
        min_level, max_level = lobby.get_min_max_overall_by_queue_time()
        self.assertEqual((0, 2), (min_level, max_level))

        mocker.return_value = 60
        min_level, max_level = lobby.get_min_max_overall_by_queue_time()
        self.assertEqual((0, 3), (min_level, max_level))

        mocker.return_value = 90
        min_level, max_level = lobby.get_min_max_overall_by_queue_time()
        self.assertEqual((0, 4), (min_level, max_level))

        mocker.return_value = 120
        min_level, max_level = lobby.get_min_max_overall_by_queue_time()
        self.assertEqual((0, 5), (min_level, max_level))

    def test_is_owner_is_true(self):
        lobby = Lobby.create(self.user_1.id)

        self.assertTrue(Lobby.is_owner(lobby.id, self.user_1.id))

    def test_is_owner_is_false(self):
        lobby = Lobby.create(self.user_1.id)

        self.assertFalse(Lobby.is_owner(lobby.id, self.user_2.id))

    def test_delete_all_keys(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertGreaterEqual(
            len(cache.keys(f'{Lobby.Config.CACHE_PREFIX}:{self.user_1.id}*')), 1
        )

        Lobby.delete(lobby.id)
        self.assertEqual(
            len(cache.keys(f'{Lobby.Config.CACHE_PREFIX}:{self.user_1.id}*')), 0
        )

    def test_start_queue(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertIsNone(lobby.queue)

        lobby.start_queue()
        self.assertIsNotNone(lobby.queue)

        player = Player.get_by_user_id(self.user_1.id)
        self.assertIsNotNone(player)
        self.assertEqual(player.user_id, self.user_1.id)


class TeamModelTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()
        self.user_7.auth.add_session()
        self.user_8.auth.add_session()
        self.user_9.auth.add_session()
        self.user_10.auth.add_session()

        self.lobby1 = Lobby.create(owner_id=self.user_1.id)
        self.lobby2 = Lobby.create(owner_id=self.user_2.id)
        self.lobby3 = Lobby.create(owner_id=self.user_3.id)
        self.lobby4 = Lobby.create(owner_id=self.user_4.id)
        self.lobby5 = Lobby.create(owner_id=self.user_5.id)
        self.lobby6 = Lobby.create(owner_id=self.user_6.id)
        self.lobby7 = Lobby.create(owner_id=self.user_7.id)
        self.lobby8 = Lobby.create(owner_id=self.user_8.id)
        self.lobby9 = Lobby.create(owner_id=self.user_9.id)
        self.lobby10 = Lobby.create(owner_id=self.user_10.id)

    def test_players_count(self):
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
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
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)
        self.assertEqual(team.players_count, self.lobby1.max_players)

    def test_build_skips(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)

        self.lobby4.set_public()
        Lobby.move(self.user_5.id, self.lobby4.id)

        self.lobby1.start_queue()
        self.lobby4.set_mode(1)
        self.lobby4.start_queue()
        self.lobby6.start_queue()

        team = Team.build(self.lobby1)
        self.assertEqual(team.lobbies_ids, [self.lobby1.id, self.lobby6.id])
        self.assertEqual(team.players_count, 4)
        team.delete()

        self.user_6.account.level = 7
        self.user_6.account.save()

        team = Team.build(self.lobby1)
        self.assertIsNone(team)

    def test_ready(self):
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        self.assertFalse(team1.ready)

        team2 = Team.create(
            lobbies_ids=[
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
                self.lobby6.id,
            ]
        )

        self.assertTrue(team2.ready)

    def test_build_errors(self):
        Team.create(lobbies_ids=[self.lobby1.id])
        Team.create(lobbies_ids=[self.lobby2.id, self.lobby4.id])

        with self.assertRaises(TeamException):
            Team.build(self.lobby1)

        with self.assertRaises(TeamException):
            Team.build(self.lobby2)

        with self.assertRaises(TeamException):
            Team.build(self.lobby3)

        with self.assertRaises(TeamException):
            Team.build(self.lobby4)

        self.lobby5.start_queue()
        Team.build(self.lobby5)

    def test_get_all(self):
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        team2 = Team.create(lobbies_ids=[self.lobby2.id])
        team3 = Team.create(
            lobbies_ids=[self.lobby3.id, self.lobby4.id, self.lobby5.id, self.lobby6.id]
        )

        teams = Team.get_all()
        self.assertCountEqual(teams, [team1, team2, team3])

    def test_remove_lobby(self):
        team = Team.create(
            lobbies_ids=[
                self.lobby1.id,
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
            ]
        )
        team.remove_lobby(self.lobby3.id)
        self.assertFalse(team.ready)
        self.assertTrue(self.lobby3.id not in team.lobbies_ids)

        team.remove_lobby(self.lobby2.id)
        team.remove_lobby(self.lobby4.id)
        team.remove_lobby(self.lobby5.id)

        with self.assertRaises(TeamException):
            Team.get_by_id(team.id)

    def test_create_and_get_by_id(self):
        team = Team.create(lobbies_ids=[self.lobby1.id])
        obj = Team.get_by_id(team.id)

        self.assertIsNotNone(obj)
        self.assertEqual(team.id, obj.id)

        team = Team.create(
            lobbies_ids=[
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
                self.lobby6.id,
            ]
        )
        obj = Team.get_by_id(team.id)

        self.assertIsNotNone(obj)
        self.assertEqual(team.id, obj.id)
        self.assertTrue(team.ready)

    def test_create_and_get_by_id_error(self):
        with self.assertRaises(TeamException):
            Team.create(
                lobbies_ids=[
                    self.lobby1.id,
                    self.lobby2.id,
                    self.lobby3.id,
                    self.lobby4.id,
                    self.lobby5.id,
                    self.lobby6.id,
                ]
            )

    def test_find(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team = Team.build(self.lobby1)
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)
        self.assertEqual(team.players_count, 2)
        self.assertEqual(len(team.lobbies_ids), 2)

        self.lobby3.start_queue()
        team2 = Team.find(self.lobby3)
        self.assertIsNotNone(team2)
        self.assertEqual(team.id, team2.id)

    def test_find_not_matching_overalls(self):
        self.user_3.account.level = 20
        self.user_3.account.save()

        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team = Team.build(self.lobby1)
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)
        self.assertEqual(team.players_count, 2)
        self.assertEqual(len(team.lobbies_ids), 2)

        self.lobby3.start_queue()
        team2 = Team.find(self.lobby3)
        self.assertIsNone(team2)

    def test_find_not_matching_mode(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        team = Team.build(self.lobby1)
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)

        self.lobby3.set_mode(1)
        self.lobby3.start_queue()
        team = Team.find(self.lobby3)
        self.assertIsNone(team)

    def test_overall(self):
        self.user_1.account.level = 5
        self.user_1.account.save()
        self.user_2.account.level = 4
        self.user_2.account.save()

        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team = Team.build(self.lobby1)
        self.assertEqual(team.overall, 5)

    def test_get_all_not_ready(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team1 = Team.build(self.lobby1)

        self.lobby3.start_queue()
        self.lobby6.start_queue()

        team3 = Team.build(self.lobby3)

        not_ready = Team.get_all_not_ready()
        self.assertCountEqual([team1, team3], not_ready)

    def test_get_by_lobby_id(self):
        team = Team.create(lobbies_ids=[self.lobby1.id])
        obj = Team.get_by_lobby_id(self.lobby1.id)
        self.assertEqual(team, obj)

        with self.assertRaises(TeamException):
            Team.get_by_lobby_id('unknown_lobby_id')

    def test_delete(self):
        team = Team.create(lobbies_ids=[self.lobby1.id])
        team.delete()

        with self.assertRaises(TeamException):
            Team.get_by_id(team).id

    def test_type_mode(self):
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id, self.lobby3.id])
        self.assertEqual(team.type_mode, ('competitive', 5))

    def test_min_max_overall_by_queue_time(self):
        self.lobby1.start_queue()
        now_minus_100 = (timezone.now() - datetime.timedelta(seconds=100)).isoformat()
        cache.set(f'{self.lobby1.cache_key}:queue', now_minus_100)

        self.user_2.account.level = 3
        self.user_2.account.save()
        self.lobby2.start_queue()

        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
        self.assertEqual(team.min_max_overall_by_queue_time, (0, 4))

    def test_overall_match(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
        match = Team.overall_match(team, self.lobby3)
        self.assertTrue(match)

        elapsed_time = (timezone.now() - datetime.timedelta(seconds=100)).isoformat()
        cache.set(f'{self.lobby1.cache_key}:queue', elapsed_time)
        cache.set(f'{self.lobby2.cache_key}:queue', elapsed_time)
        cache.set(f'{self.lobby3.cache_key}:queue', elapsed_time)

        self.user_4.account.level = 4
        self.user_4.account.save()
        self.lobby4.start_queue()

        match = Team.overall_match(team, self.lobby4)
        self.assertTrue(match)

    def test_overall_not_match(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])

        self.user_3.account.level = 6
        self.user_3.account.save()
        self.lobby3.start_queue()

        match = Team.overall_match(team, self.lobby3)
        self.assertFalse(match)

    def test_get_opponent_team(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)
        Lobby.move(self.user_4.id, self.lobby1.id)
        Lobby.move(self.user_5.id, self.lobby1.id)
        self.lobby1.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])

        self.lobby6.set_public()
        Lobby.move(self.user_7.id, self.lobby6.id)
        Lobby.move(self.user_8.id, self.lobby6.id)
        Lobby.move(self.user_9.id, self.lobby6.id)
        Lobby.move(self.user_10.id, self.lobby6.id)
        self.lobby6.start_queue()
        team2 = Team.create(lobbies_ids=[self.lobby6.id])

        opponent = team2.get_opponent_team()
        self.assertEqual(opponent, team1)

    def test_get_opponent_team_overall_queue_time(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)
        Lobby.move(self.user_4.id, self.lobby1.id)
        Lobby.move(self.user_5.id, self.lobby1.id)
        self.lobby1.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])

        self.user_8.account.level = 5
        self.user_8.account.save()

        self.lobby6.set_public()
        Lobby.move(self.user_7.id, self.lobby6.id)
        Lobby.move(self.user_8.id, self.lobby6.id)
        Lobby.move(self.user_9.id, self.lobby6.id)
        Lobby.move(self.user_10.id, self.lobby6.id)
        self.lobby6.start_queue()
        team = Team.create(lobbies_ids=[self.lobby6.id])

        opponent = team.get_opponent_team()
        self.assertIsNone(opponent)

        elapsed_time = (timezone.now() - datetime.timedelta(seconds=140)).isoformat()
        cache.set(f'{self.lobby1.cache_key}:queue', elapsed_time)
        opponent = team.get_opponent_team()
        self.assertEqual(opponent, team1)

    def test_name(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)
        Lobby.move(self.user_4.id, self.lobby1.id)
        Lobby.move(self.user_5.id, self.lobby1.id)
        self.lobby1.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        players_ids = [lobby.players_ids for lobby in team1.lobbies][0]
        players_usernames = [
            User.objects.get(pk=player_id).steam_user.username
            for player_id in players_ids
        ]
        self.assertIsNotNone(team1.name)
        self.assertTrue(team1.name in players_usernames)


class LobbyInviteModelTestCase(mixins.VerifiedPlayersMixin, TestCase):
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

    def test_get_all(self):
        invites = LobbyInvite.get_all()
        self.assertCountEqual(invites, [])

        self.lobby1.invite(self.user_1.id, self.user_2.id)
        invites = LobbyInvite.get_all()
        self.assertCountEqual(
            invites,
            [
                LobbyInvite(
                    from_id=self.user_1.id,
                    to_id=self.user_2.id,
                    lobby_id=self.lobby1.id,
                )
            ],
        )

        self.lobby1.invite(self.user_1.id, self.user_3.id)
        invites = LobbyInvite.get_all()
        self.assertCountEqual(
            invites,
            [
                LobbyInvite(
                    from_id=self.user_1.id,
                    to_id=self.user_2.id,
                    lobby_id=self.lobby1.id,
                ),
                LobbyInvite(
                    from_id=self.user_1.id,
                    to_id=self.user_3.id,
                    lobby_id=self.lobby1.id,
                ),
            ],
        )

        self.lobby5.invite(self.user_5.id, self.user_4.id)
        invites = LobbyInvite.get_all()
        self.assertCountEqual(
            invites,
            [
                LobbyInvite(
                    from_id=self.user_1.id,
                    to_id=self.user_2.id,
                    lobby_id=self.lobby1.id,
                ),
                LobbyInvite(
                    from_id=self.user_1.id,
                    to_id=self.user_3.id,
                    lobby_id=self.lobby1.id,
                ),
                LobbyInvite(
                    from_id=self.user_5.id,
                    to_id=self.user_4.id,
                    lobby_id=self.lobby5.id,
                ),
            ],
        )

    def test_get_by_to_user_id(self):
        invites = LobbyInvite.get_by_to_user_id(self.user_2.id)
        self.assertCountEqual(invites, [])

        self.lobby1.invite(self.user_1.id, self.user_2.id)
        invites = LobbyInvite.get_by_to_user_id(self.user_2.id)
        self.assertCountEqual(
            invites,
            [
                LobbyInvite(
                    from_id=self.user_1.id,
                    to_id=self.user_2.id,
                    lobby_id=self.lobby1.id,
                )
            ],
        )

        self.lobby3.invite(self.user_3.id, self.user_2.id)
        invites = LobbyInvite.get_by_to_user_id(self.user_2.id)
        self.assertCountEqual(
            invites,
            [
                LobbyInvite(
                    from_id=self.user_1.id,
                    to_id=self.user_2.id,
                    lobby_id=self.lobby1.id,
                ),
                LobbyInvite(
                    from_id=self.user_3.id,
                    to_id=self.user_2.id,
                    lobby_id=self.lobby3.id,
                ),
            ],
        )


class PreMatchModelTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()
        self.user_7.auth.add_session()
        self.user_8.auth.add_session()
        self.user_9.auth.add_session()
        self.user_10.auth.add_session()
        self.user_11.auth.add_session()
        self.user_12.auth.add_session()
        self.user_13.auth.add_session()
        self.user_14.auth.add_session()
        self.user_15.auth.add_session()

        self.lobby1 = Lobby.create(owner_id=self.user_1.id)
        self.lobby2 = Lobby.create(owner_id=self.user_2.id)
        self.lobby3 = Lobby.create(owner_id=self.user_3.id)
        self.lobby4 = Lobby.create(owner_id=self.user_4.id)
        self.lobby5 = Lobby.create(owner_id=self.user_5.id)
        self.lobby6 = Lobby.create(owner_id=self.user_6.id)
        self.lobby7 = Lobby.create(owner_id=self.user_7.id)
        self.lobby8 = Lobby.create(owner_id=self.user_8.id)
        self.lobby9 = Lobby.create(owner_id=self.user_9.id)
        self.lobby10 = Lobby.create(owner_id=self.user_10.id)
        self.lobby11 = Lobby.create(owner_id=self.user_11.id)
        self.lobby12 = Lobby.create(owner_id=self.user_12.id)
        self.lobby13 = Lobby.create(owner_id=self.user_13.id)
        self.lobby14 = Lobby.create(owner_id=self.user_14.id)
        self.lobby15 = Lobby.create(owner_id=self.user_15.id)

        self.team1 = Team.create(
            [
                self.lobby1.id,
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
            ]
        )
        self.team2 = Team.create(
            [
                self.lobby6.id,
                self.lobby7.id,
                self.lobby8.id,
                self.lobby9.id,
                self.lobby10.id,
            ]
        )

    def test_create(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        match_model = PreMatch.get_by_id(match.id)
        self.assertEqual(match, match_model)

    def test_start_players_ready_countdown(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        ready_time = cache.get(f'{match.cache_key}:ready_time')
        self.assertIsNone(ready_time)

        match.start_players_ready_countdown()
        ready_time = cache.get(f'{match.cache_key}:ready_time')
        self.assertIsNotNone(ready_time)

    def test_set_player_ready(self):
        match = PreMatch.create(self.team1.id, self.team2.id)

        for _ in range(0, settings.MATCH_READY_PLAYERS_MIN):
            match.set_player_lock_in()
        match.start_players_ready_countdown()
        self.assertEqual(len(match.players_ready), 0)

        match.set_player_ready(self.user_1.id)
        self.assertEqual(len(match.players_ready), 1)

    def test_set_player_ready_wrong_state(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        with self.assertRaises(PreMatchException):
            match.set_player_ready(self.user_1.id)

    def test_set_player_lock_in(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(match.players_in, 0)

        match.set_player_lock_in()
        self.assertEqual(match.players_in, 1)

    def test_set_player_lock_in_wrong_state(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        for _ in range(0, settings.MATCH_READY_PLAYERS_MIN):
            match.set_player_lock_in()

        with self.assertRaises(PreMatchException):
            match.set_player_lock_in()

    def test_state(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(match.state, PreMatchConfig.STATES.get('pre_start'))

        for _ in range(0, settings.MATCH_READY_PLAYERS_MIN):
            match.set_player_lock_in()
        self.assertEqual(match.state, PreMatchConfig.STATES.get('idle'))

        match.start_players_ready_countdown()
        self.assertEqual(match.state, PreMatchConfig.STATES.get('lock_in'))

        for player in match.players:
            match.set_player_ready(player.id)

        self.assertEqual(match.state, PreMatchConfig.STATES.get('ready'))

    def test_state_canceled(self):
        match = PreMatch.create(self.team1.id, self.team2.id)

        for _ in range(0, settings.MATCH_READY_PLAYERS_MIN):
            match.set_player_lock_in()

        past_time = (timezone.now() - timezone.timedelta(seconds=30)).isoformat()
        cache.set(f'{match.cache_key}:ready_time', past_time)

        self.assertEqual(match.state, PreMatchConfig.STATES.get('lock_in'))

    def test_countdown(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        match.start_players_ready_countdown()
        self.assertEqual(match.countdown, 30)
        time.sleep(2)
        self.assertEqual(match.countdown, 28)

    def test_teams(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(match.teams[0], self.team1)
        self.assertEqual(match.teams[1], self.team2)

    def test_players(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(len(match.players), 10)

    def test_get_by_team_id(self):
        match = PreMatch.create(self.team1.id, self.team2.id)

        result1 = PreMatch.get_by_team_id(self.team1.id)
        self.assertEqual(match, result1)

        result2 = PreMatch.get_by_team_id(self.team2.id)
        self.assertEqual(match, result2)

        result3 = PreMatch.get_by_team_id(self.team1.id, self.team2.id)
        self.assertEqual(match, result3)

    def test_delete_all_keys(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertGreaterEqual(len(cache.keys(f'{match.cache_key}*')), 1)

        PreMatch.delete(match.id)
        self.assertGreaterEqual(len(cache.keys(f'{match.cache_key}*')), 0)

    def test_get_all(self):
        all_matches = PreMatch.get_all()
        self.assertEqual(len(all_matches), 0)

        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        pre_match.start_players_ready_countdown()
        all_matches = PreMatch.get_all()
        self.assertEqual(len(all_matches), 1)

    def test_get_by_player_id(self):
        PreMatch.create(self.team1.id, self.team2.id)
        pre_match = PreMatch.get_by_player_id(player_id=self.user_1.id)
        self.assertIsNotNone(pre_match)

        pre_match = PreMatch.get_by_player_id(player_id=self.user_15.id)
        self.assertIsNone(pre_match)


class PlayerModelTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def test_create(self):
        player = Player.create(self.user_1.id)
        self.assertIsNotNone(player)
        self.assertEqual(player.user_id, self.user_1.id)
        self.assertTrue(cache.sismember('__mm:players', self.user_1.id))

    def test_get_all(self):
        Player.create(self.user_1.id)
        Player.create(self.user_2.id)
        Player.create(self.user_3.id)

        self.assertEqual(len(Player.get_all()), 3)

    def test_get_by_user_id(self):
        Player.create(self.user_2.id)

        with self.assertRaises(PlayerException):
            Player.get_by_user_id(self.user_1.id)

        player = Player.get_by_user_id(self.user_2.id)
        self.assertEqual(self.user_2.id, player.user_id)

    def test_dodge_add(self):
        player = Player.create(self.user_1.id)
        self.assertEqual(player.dodges, 0)
        player.dodge_add()
        self.assertEqual(player.dodges, 1)
        player.dodge_add()
        self.assertEqual(player.dodges, 2)

        player.dodge_add()
        self.assertEqual(player.dodges, 3)

        ttl = cache.ttl(f'{player.cache_key}:dodges')
        self.assertEqual(ttl, Player.Config.DODGES_EXPIRE_TIME)

        self.assertIsNotNone(player.lock_date)

        with self.assertRaises(PlayerException):
            player.dodge_add()

        cache.delete(f'{player.cache_key}:queue_lock')

        player.dodge_add()
        self.assertEqual(player.dodges, 4)

    def test_dodge_clear(self):
        player = Player.create(self.user_1.id)
        player.dodge_add()
        player.dodge_add()
        self.assertEqual(player.dodges, 2)
        player.dodge_clear()
        self.assertEqual(player.dodges, 0)

    def test_latest_dodge(self):
        player = Player.create(self.user_1.id)
        cache.zadd(
            f'{player.cache_key}:dodges',
            {'2023-04-06T16:40:31.610866+00:00': 1680800659.26437},
        )
        self.assertEqual(
            player.latest_dodge, str_to_timezone('2023-04-06T16:40:31.610866+00:00')
        )

        cache.zadd(
            f'{player.cache_key}:dodges',
            {'2023-05-06T16:40:31.610866+00:00': 1780800659.26437},
        )
        cache.zadd(
            f'{player.cache_key}:dodges',
            {'2023-06-06T16:40:31.610866+00:00': 1880800659.26437},
        )
        cache.zadd(
            f'{player.cache_key}:dodges',
            {'2023-03-06T16:40:31.610866+00:00': 1980800659.26437},
        )
        self.assertEqual(
            player.latest_dodge, str_to_timezone('2023-03-06T16:40:31.610866+00:00')
        )

    def test_delete(self):
        Player.create(user_id=self.user_1.id)
        Player.delete(self.user_1.id)
        self.assertFalse(cache.sismember('__mm:players', self.user_1.id))

    def test_lock_countdown(self):
        player = Player.create(user_id=self.user_1.id)
        delta = timezone.timedelta(minutes=15)
        cache.set(
            f'{player.cache_key}:queue_lock',
            (timezone.now() + delta).isoformat(),
        )
        self.assertEqual(player.lock_countdown, 60 * 15 - 1)
