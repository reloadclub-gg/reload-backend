from time import sleep
from unittest import mock

from django.test import override_settings
from django.utils import timezone

from accounts.tests.mixins import VerifiedAccountsMixin
from appsettings.models import AppSettings
from core.tests import TestCase, cache

from ..models import (
    Lobby,
    LobbyException,
    LobbyInvite,
    LobbyInviteException,
    PlayerRestriction,
)
from ..tasks import handle_dodges


class LobbyModelTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.add_session()
        self.user_2.add_session()
        self.user_3.add_session()
        self.user_4.add_session()
        self.user_5.add_session()
        self.user_6.add_session()
        self.online_noaccount_user.add_session()
        self.online_unverified_user.add_session()

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
        self.assertEqual(lobby.mode, Lobby.ModeChoices.COMP)

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
        invites = list(cache.zrange(f'{lobby_1.cache_key}:invites', 0, -1))
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
        self.assertEqual(len(cache.zrange(f'{lobby_1.cache_key}:invites', 0, -1)), 0)
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
        self.assertEqual(len(cache.zrange(f'{lobby_2.cache_key}:invites', 0, -1)), 0)
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
        self.assertEqual(len(cache.zrange(f'{lobby_2.cache_key}:invites', 0, -1)), 0)
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
        self.assertEqual(len(cache.zrange(f'{lobby_2.cache_key}:invites', 0, -1)), 0)
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

    def test_move_remove_remaining(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.set_public()
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)

        Lobby.move(self.user_2.id, lobby.id)
        Lobby.move(self.user_3.id, lobby.id)

        Lobby.move(self.user_1.id, lobby.id, remove=True)

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
            lobby.max_players,
            Lobby.Config.MAX_SEATS.get(Lobby.ModeChoices.COMP),
        )

        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        self.assertEqual(
            lobby.max_players,
            Lobby.Config.MAX_SEATS.get(Lobby.ModeChoices.CUSTOM),
        )

    def test_set_mode(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertEqual(lobby.mode, Lobby.ModeChoices.COMP)
        self.assertEqual(lobby.def_players_ids, [])
        self.assertIsNone(lobby.match_type)
        self.assertIsNone(lobby.map_id)

        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        self.assertEqual(lobby.mode, Lobby.ModeChoices.CUSTOM)
        self.assertEqual(lobby.def_players_ids, [self.user_1.id])
        self.assertEqual(lobby.match_type, Lobby.TypeChoices.DEFAULT)
        self.assertEqual(lobby.map_id, Lobby.Config.MAPS.get(lobby.match_type)[0])

        lobby.set_mode(Lobby.ModeChoices.COMP)
        self.assertEqual(lobby.mode, Lobby.ModeChoices.COMP)
        self.assertEqual(lobby.def_players_ids, [])
        self.assertIsNone(lobby.match_type)
        self.assertIsNone(lobby.map_id)

    def test_set_mode_right_seat_after_join(self):
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

        lobby_1.set_mode(Lobby.ModeChoices.CUSTOM)

        self.assertEqual(len(lobby_1.def_players_ids), 5)
        self.assertEqual(len(lobby_1.atk_players_ids), 0)
        self.assertEqual(len(lobby_1.spec_players_ids), 0)

    def test_set_mode_right_seat_before_join(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_1.set_mode(Lobby.ModeChoices.CUSTOM)
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

        self.assertEqual(len(lobby_1.def_players_ids), 5)
        self.assertEqual(len(lobby_1.atk_players_ids), 0)
        self.assertEqual(len(lobby_1.spec_players_ids), 0)

    def test_set_mode_same_mode(self):
        lobby = Lobby.create(self.user_1.id)
        with self.assertRaisesRegex(LobbyException, 'Mode already set'):
            lobby.set_mode(Lobby.ModeChoices.COMP)

    def test_set_mode_queued(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.start_queue()
        with self.assertRaisesRegex(LobbyException, 'queued'):
            lobby.set_mode(Lobby.ModeChoices.CUSTOM)

    def test_set_mode_oversized(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_1.set_mode(Lobby.ModeChoices.CUSTOM)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_3 = Lobby.create(self.user_3.id)
        lobby_4 = Lobby.create(self.user_4.id)
        lobby_5 = Lobby.create(self.user_5.id)
        lobby_6 = Lobby.create(self.user_6.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_3.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        lobby_1.invite(self.user_1.id, self.user_5.id)
        lobby_1.invite(self.user_1.id, self.user_6.id)

        Lobby.move(lobby_2.id, lobby_1.id)
        Lobby.move(lobby_3.id, lobby_1.id)
        Lobby.move(lobby_4.id, lobby_1.id)
        Lobby.move(lobby_5.id, lobby_1.id)
        Lobby.move(lobby_6.id, lobby_1.id)

        with self.assertRaisesRegex(LobbyException, 'oversized'):
            lobby_1.set_mode(Lobby.ModeChoices.COMP)

    def test_set_mode_unknown(self):
        lobby = Lobby.create(self.user_1.id)
        with self.assertRaises(LobbyException):
            lobby.set_mode('unknown')

        self.assertEqual(lobby.mode, Lobby.ModeChoices.COMP)

    def test_set_match_type(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertIsNone(lobby.match_type)
        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        self.assertEqual(lobby.match_type, Lobby.TypeChoices.DEFAULT)

    def test_set_match_type_bad_mode(self):
        lobby = Lobby.create(self.user_1.id)
        with self.assertRaises(LobbyException):
            lobby.set_match_type('change type in this mode')

        self.assertIsNone(lobby.match_type)

    def test_set_match_type_queued(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.start_queue()
        with self.assertRaises(LobbyException):
            lobby.set_match_type('queued')

        self.assertIsNone(lobby.match_type)

    def test_set_match_type_unknown(self):
        lobby = Lobby.create(self.user_1.id)
        with self.assertRaises(LobbyException):
            lobby.set_match_type('unknown')

        self.assertIsNone(lobby.match_type)

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

    @mock.patch('lobbies.models.lobby.Lobby.queue_time', new_callable=mock.PropertyMock)
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

    @override_settings(
        PLAYER_DODGES_MIN_TO_RESTRICT=1,
        PLAYER_DODGES_MULTIPLIER=[1, 2, 5, 10, 20, 40, 60, 90],
    )
    def test_start_queue(self):
        AppSettings.objects.create(
            kind=AppSettings.BOOLEAN,
            name='Dodges Restriction',
            value='1',
        )
        lobby = Lobby.create(self.user_1.id)
        lobby.set_public()
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.move(self.user_2.id, lobby.id)
        Lobby.move(self.user_3.id, lobby.id)
        Lobby.move(self.user_4.id, lobby.id)

        self.assertIsNone(lobby.queue)
        lobby.start_queue()
        self.assertIsNotNone(lobby.queue)
        lobby.cancel_queue()

        handle_dodges(lobby, [])
        handle_dodges(lobby, [])
        handle_dodges(lobby, [])

        with self.assertRaises(LobbyException):
            lobby.start_queue()

    def test_cancel_all_queues(self):
        lobby1 = Lobby.create(self.user_1.id)
        lobby2 = Lobby.create(self.user_2.id)
        lobby3 = Lobby.create(self.user_3.id)
        lobby4 = Lobby.create(self.user_4.id)
        lobby1.start_queue()
        lobby2.start_queue()
        lobby3.start_queue()

        self.assertIsNotNone(lobby1.queue)
        self.assertIsNotNone(lobby2.queue)
        self.assertIsNotNone(lobby3.queue)
        self.assertIsNone(lobby4.queue)

        Lobby.cancel_all_queues()

        self.assertIsNone(lobby1.queue)
        self.assertIsNone(lobby2.queue)
        self.assertIsNone(lobby3.queue)
        self.assertIsNone(lobby4.queue)

    def test_set_map_id(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        lobby.set_map_id(Lobby.Config.MAPS.get(lobby.match_type)[2])
        self.assertEqual(lobby.map_id, Lobby.Config.MAPS.get(lobby.match_type)[2])

    def test_set_map_id_bad_mode(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        with self.assertRaisesRegex(LobbyException, 'Cannot restrict map'):
            lobby.set_map_id(2)

    def test_set_map_id_invalid(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        with self.assertRaisesRegex(LobbyException, 'Invalid map id'):
            lobby.set_map_id(9)

    def test_set_weapon(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        self.assertIsNone(lobby.weapon)
        lobby.set_weapon(Lobby.WeaponChoices.WEAPON_APPISTOL)
        self.assertEqual(lobby.weapon, Lobby.WeaponChoices.WEAPON_APPISTOL)

        lobby.set_weapon()
        self.assertIsNone(lobby.weapon)

    def test_set_weapon_bad_mode(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        with self.assertRaisesRegex(LobbyException, 'Cannot restrict weapon'):
            lobby.set_weapon(Lobby.WeaponChoices.WEAPON_APPISTOL)

    def test_set_weapon_invalid(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        with self.assertRaisesRegex(LobbyException, 'Invalid weapon'):
            lobby.set_weapon('any_weapon')

    def test_change_player_side(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        self.assertCountEqual(lobby.def_players_ids, [self.user_1.id])
        self.assertCountEqual(lobby.atk_players_ids, [])
        self.assertCountEqual(lobby.spec_players_ids, [])

        lobby.change_player_side(self.user_1.id, 'atk_players_ids')
        self.assertCountEqual(lobby.atk_players_ids, [self.user_1.id])
        self.assertCountEqual(lobby.def_players_ids, [])
        self.assertCountEqual(lobby.spec_players_ids, [])

        lobby.change_player_side(self.user_1.id, 'spec_players_ids')
        self.assertCountEqual(lobby.spec_players_ids, [self.user_1.id])
        self.assertCountEqual(lobby.def_players_ids, [])
        self.assertCountEqual(lobby.atk_players_ids, [])

        lobby.change_player_side(self.user_1.id, 'def_players_ids')
        self.assertCountEqual(lobby.def_players_ids, [self.user_1.id])
        self.assertCountEqual(lobby.spec_players_ids, [])
        self.assertCountEqual(lobby.atk_players_ids, [])

    def test_change_player_side_bad_mode(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        with self.assertRaisesRegex(LobbyException, 'Cannot change side'):
            lobby.change_player_side(self.user_1.id, 'def_players_ids')

    def test_change_player_side_player_not_found(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        with self.assertRaisesRegex(LobbyException, 'Player not found'):
            lobby.change_player_side(self.user_5.id, 'def_players_ids')

    def test_change_player_side_bad_side(self):
        lobby = Lobby.create(owner_id=self.user_1.id)
        lobby.set_mode(Lobby.ModeChoices.CUSTOM)
        with self.assertRaisesRegex(LobbyException, 'Invalid side'):
            lobby.change_player_side(self.user_1.id, 'attackers')

    def test_change_player_side_oversized(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_3 = Lobby.create(self.user_3.id)
        lobby_4 = Lobby.create(self.user_4.id)
        lobby_5 = Lobby.create(self.user_5.id)
        lobby_6 = Lobby.create(self.user_6.id)
        lobby_1.set_mode(Lobby.ModeChoices.CUSTOM)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_3.id)
        lobby_1.invite(self.user_1.id, self.user_4.id)
        lobby_1.invite(self.user_1.id, self.user_5.id)
        lobby_1.invite(self.user_1.id, self.user_6.id)

        Lobby.move(lobby_2.id, lobby_1.id)
        Lobby.move(lobby_3.id, lobby_1.id)
        Lobby.move(lobby_4.id, lobby_1.id)
        Lobby.move(lobby_5.id, lobby_1.id)
        Lobby.move(lobby_6.id, lobby_1.id)

        with self.assertRaisesRegex(LobbyException, 'Side is full'):
            lobby_1.change_player_side(self.user_6.id, 'def_players_ids')

    def test_change_player_side_player_already_on_side(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_1.set_mode(Lobby.ModeChoices.CUSTOM)

        with self.assertRaisesRegex(LobbyException, 'already on side'):
            lobby_1.change_player_side(self.user_1.id, 'def_players_ids')


class LobbyInviteModelTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.add_session()
        self.user_2.add_session()
        self.user_3.add_session()
        self.user_4.add_session()
        self.user_5.add_session()
        self.user_6.add_session()

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

    def test_create_date(self):
        timestamp = timezone.now().timestamp()
        cache.zadd(
            f'{self.lobby1.cache_key}:invites',
            {f'{self.user_1.id}:{self.user_2.id}': timestamp},
        )
        invite = LobbyInvite(
            from_id=self.user_1.id, to_id=self.user_2.id, lobby_id=self.lobby1.id
        )
        self.assertEqual(invite.create_date, timezone.datetime.fromtimestamp(timestamp))

    def test_get_by_id(self):
        created = self.lobby1.invite(self.user_1.id, self.user_2.id)
        invite = LobbyInvite.get_by_id(f'{self.user_1.id}:{self.user_2.id}')
        self.assertEqual(created.id, invite.id)

        with self.assertRaises(LobbyInviteException):
            LobbyInvite.get_by_id('some_id:other_id')

    def test_delete(self):
        created = self.lobby1.invite(self.user_1.id, self.user_2.id)
        LobbyInvite.delete(created)

        with self.assertRaises(LobbyInviteException):
            LobbyInvite.get_by_id(created.id)


class PlayerModelTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.add_session()
        self.user_2.add_session()

    @override_settings(
        PLAYER_DODGES_MIN_TO_RESTRICT=3,
        PLAYER_DODGES_MULTIPLIER=[1, 2, 5, 10, 20, 40, 60, 90],
    )
    def test_restriction_countdown(self):
        AppSettings.objects.create(
            kind=AppSettings.BOOLEAN,
            name='Dodges Restriction',
            value='1',
        )
        lobby = Lobby.create(self.user_1.id)
        lobby.set_public()
        Lobby.create(self.user_2.id)
        Lobby.move(self.user_2.id, lobby.id)

        self.assertIsNone(lobby.restriction_countdown)
        handle_dodges(lobby, [self.user_1.id])
        self.assertIsNone(lobby.restriction_countdown)
        handle_dodges(lobby, [self.user_1.id])
        self.assertIsNone(lobby.restriction_countdown)
        handle_dodges(lobby, [self.user_1.id])
        restriction = PlayerRestriction.objects.get(user=self.user_2)
        self.assertEqual(
            lobby.restriction_countdown,
            (restriction.end_date - timezone.now()).seconds,
        )
        handle_dodges(lobby, [self.user_2.id])
        handle_dodges(lobby, [self.user_2.id])
        handle_dodges(lobby, [self.user_2.id])
        handle_dodges(lobby, [self.user_2.id])
        restriction = PlayerRestriction.objects.get(user=self.user_1)
        self.assertEqual(
            lobby.restriction_countdown,
            (restriction.end_date - timezone.now()).seconds,
        )
