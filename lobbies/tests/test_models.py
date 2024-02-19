from datetime import timedelta
from time import sleep

from django.utils import timezone

from accounts.tests.mixins import VerifiedAccountsMixin
from appsettings.services import (
    lobby_overall_range,
    lobby_time_to_increase_overall_range,
)
from core.tests import TestCase, cache

from .. import models


class LobbyModelTestCase(VerifiedAccountsMixin, TestCase):

    def test_create(self):
        lobby = models.Lobby.create(self.user_1.id)
        self.assertEqual(lobby.owner_id, self.user_1.id)
        self.assertEqual(lobby.id, lobby.owner_id)
        self.assertEqual(lobby.players_ids, [self.user_1.id])
        self.assertEqual(lobby.mode, 'competitive')

        lobby2 = models.Lobby.create(self.user_2.id, mode='custom')
        self.assertEqual(lobby2.owner_id, self.user_2.id)
        self.assertEqual(lobby2.id, lobby2.owner_id)
        self.assertEqual(lobby2.players_ids, [self.user_2.id])
        self.assertEqual(lobby2.mode, 'custom')

    def test_create_duplicate(self):
        models.Lobby.create(self.user_1.id)
        with self.assertRaisesRegex(
            models.LobbyException, 'Player already have a lobby'
        ):
            models.Lobby.create(self.user_1.id)

    def test_create_bad_mode(self):
        with self.assertRaisesRegex(models.LobbyException, 'Mode must be'):
            models.Lobby.create(self.user_1.id, mode='bad_mode')

    def test_save(self):
        lobby = models.Lobby(owner_id=self.user_1.id)
        self.assertEqual(lobby.owner_id, self.user_1.id)
        self.assertEqual(lobby.id, lobby.owner_id)
        self.assertEqual(lobby.players_ids, [])
        self.assertEqual(lobby.mode, 'competitive')

        with self.assertRaises(models.LobbyException):
            models.Lobby.get(self.user_1.id)

        non_saved_lobby = models.Lobby.get(self.user_1.id, fail_silently=True)
        self.assertIsNone(non_saved_lobby)

        lobby.save()

        saved_lobby = models.Lobby.get(self.user_1.id)
        self.assertEqual(saved_lobby, lobby)

        lobby2 = models.Lobby(owner_id=self.user_1.id, mode='custom')
        self.assertEqual(lobby2.mode, 'custom')

    def test_save_pre_match(self):
        lobby = models.Lobby.create(self.user_1.id)
        cache.set(f'{lobby.cache_key}:pre_match_id', 1)
        with self.assertRaisesRegex(models.LobbyException, 'while in match'):
            lobby.save()

        cache.delete(f'{lobby.cache_key}:pre_match_id')
        lobby.save()

    def test_add_player(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        self.assertEqual(lobby.players_ids, [self.user_1.id])

        lobby.update_visibility('public')
        lobby.add_player(self.user_2.id)
        self.assertEqual(lobby.players_ids, [self.user_1.id, self.user_2.id])

    def test_add_player_full(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        lobby.update_visibility('public')
        lobby.add_player(self.user_2.id)
        lobby.add_player(self.user_3.id)
        lobby.add_player(self.user_4.id)
        lobby.add_player(self.user_5.id)

        with self.assertRaisesRegex(models.LobbyException, 'is full'):
            lobby.add_player(self.user_6.id)

    def test_add_player_already_in_lobby(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        lobby.update_visibility('public')
        with self.assertRaisesRegex(models.LobbyException, 'already in the lobby'):
            lobby.add_player(self.user_1.id)

    def test_add_player_not_invited(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        with self.assertRaisesRegex(models.LobbyException, 'must be invited'):
            lobby.add_player(self.user_2.id)

    def test_remove_player(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        lobby.update_visibility('public')
        lobby.add_player(self.user_2.id)
        self.assertEqual(lobby.players_ids, [self.user_1.id, self.user_2.id])

        lobby.remove_player(self.user_2.id)
        self.assertEqual(lobby.players_ids, [self.user_1.id])

    def test_remove_player_not_found(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        with self.assertRaisesRegex(models.LobbyException, 'not found'):
            lobby.remove_player(self.user_2.id)

    def test_update_queue(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)

        self.assertFalse(lobby.is_queued)
        self.assertIsNone(lobby.queue_time)

        lobby.update_queue(action='start')
        self.assertTrue(lobby.is_queued)
        self.assertIsNotNone(lobby.queue_time)
        sleep(1)
        self.assertEqual(lobby.queue_time, 1)

        lobby.update_queue(action='stop')
        self.assertFalse(lobby.is_queued)
        self.assertIsNone(lobby.queue_time)

    def test_update_queue_bad_action(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        self.assertFalse(lobby.is_queued)
        self.assertIsNone(lobby.queue_time)

        with self.assertRaisesRegex(models.LobbyException, 'started or stoped.'):
            lobby.update_queue(action='init')

        self.assertFalse(lobby.is_queued)
        self.assertIsNone(lobby.queue_time)

    def test_update_queue_pre_match(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        lobby.update_queue(action='start')
        self.assertTrue(lobby.is_queued)

        cache.set(f'{lobby.cache_key}:pre_match_id', 1)
        with self.assertRaisesRegex(models.LobbyException, 'while in match'):
            lobby.update_queue(action='stop')

        self.assertTrue(lobby.is_queued)

    def test_update_mode(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        self.assertEqual(lobby.mode, models.Lobby.ModeChoices.COMPETITIVE)

        lobby.update_mode(models.Lobby.ModeChoices.COMPETITIVE)
        self.assertEqual(lobby.mode, models.Lobby.ModeChoices.COMPETITIVE)

        lobby.update_mode(models.Lobby.ModeChoices.CUSTOM)
        self.assertEqual(lobby.mode, models.Lobby.ModeChoices.CUSTOM)

    def test_update_mode_bad_mode(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        self.assertEqual(lobby.mode, models.Lobby.ModeChoices.COMPETITIVE)

        with self.assertRaisesRegex(models.LobbyException, 'Mode must be'):
            lobby.update_mode('bad_mode')

        self.assertEqual(lobby.mode, models.Lobby.ModeChoices.COMPETITIVE)

    def test_get_queue_overall_range(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        lobby.update_queue(action='start')
        self.assertEqual(lobby.get_queue_overall_range(), (0, 3))
        lobby.update_queue(action='stop')

        with self.assertRaisesRegex(models.LobbyException, 'Lobby must be queued'):
            lobby.get_queue_overall_range()

        queue_start_time = timezone.now() - timedelta(
            seconds=lobby_time_to_increase_overall_range()[0] - 1
        )
        expected_overall = (
            max(lobby.overall - lobby_overall_range()[0], 0),
            lobby.overall + lobby_overall_range()[0],
        )
        cache.set(f'{lobby.cache_key}:queue', queue_start_time.isoformat())
        self.assertEqual(lobby.get_queue_overall_range(), expected_overall)

    def test_load(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        model = models.Lobby.load(lobby.cache_key)
        self.assertEqual(lobby, model)

    def test_delete(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)
        self.assertTrue(cache.exists(lobby.cache_key))

        lobby.delete()
        self.assertFalse(cache.exists(lobby.cache_key))
        self.assertIsNone(
            models.Lobby.get_by_player_id(
                self.user_1.id,
                fail_silently=True,
            )
        )

    def test_delete_pre_match(self):
        lobby = models.Lobby.create(owner_id=self.user_1.id)

        cache.set(f'{lobby.cache_key}:pre_match_id', 1)
        with self.assertRaisesRegex(models.LobbyException, 'while in match'):
            lobby.delete()
        self.assertTrue(cache.exists(lobby.cache_key))

        cache.delete(f'{lobby.cache_key}:pre_match_id')
        lobby.delete()
        self.assertFalse(cache.exists(lobby.cache_key))

    def test_get(self):
        with self.assertRaisesRegex(models.LobbyException, 'not found'):
            models.Lobby.get(self.user_1.id)

        lobby = models.Lobby.get(self.user_1.id, fail_silently=True)
        self.assertIsNone(lobby)

        lobby = models.Lobby.create(self.user_1.id)
        model = models.Lobby.get(self.user_1.id)
        self.assertEqual(lobby, model)

    def test_get_by_player_id(self):
        with self.assertRaisesRegex(models.LobbyException, 'not found'):
            models.Lobby.get_by_player_id(self.user_1.id)

        lobby = models.Lobby.get_by_player_id(self.user_1.id, fail_silently=True)
        self.assertIsNone(lobby)

        lobby = models.Lobby.create(self.user_1.id)
        model = models.Lobby.get_by_player_id(self.user_1.id)
        self.assertEqual(lobby.id, model.id)

        lobby.update_visibility('public')
        lobby.add_player(self.user_2.id)
        model = models.Lobby.get_by_player_id(self.user_2.id)
        self.assertEqual(lobby.id, model.id)

    def test_move_player(self):
        l1 = models.Lobby.create(self.user_1.id)
        l1.update_visibility('public')
        l1.add_player(self.user_2.id)

        l2 = models.Lobby.create(self.user_3.id)
        l2.update_visibility('public')
        l2.add_player(self.user_4.id)

        l1, l2, _ = models.Lobby.move_player(self.user_2.id, self.user_3.id)
        self.assertCountEqual(l1.players_ids, [self.user_1.id])
        self.assertCountEqual(
            l2.players_ids,
            [self.user_2.id, self.user_3.id, self.user_4.id],
        )

    def test_move_player_owner(self):
        models.Lobby.create(self.user_2.id)
        l1 = models.Lobby.create(self.user_1.id)
        l2 = models.Lobby.create(self.user_3.id)
        l1.update_visibility(visibility='public')
        l2.update_visibility(visibility='public')

        from_lobby, to_lobby, _ = models.Lobby.move_player(self.user_2.id, l1.owner_id)
        self.assertEqual(len(from_lobby.players_ids), 0)
        self.assertEqual(len(to_lobby.players_ids), 2)

        from_lobby, to_lobby, remaining_lobby = models.Lobby.move_player(
            self.user_1.id,
            l2.owner_id,
        )

        self.assertCountEqual(from_lobby.players_ids, [])
        self.assertEqual(from_lobby.owner_id, self.user_1.id)

        self.assertCountEqual(to_lobby.players_ids, [self.user_1.id, self.user_3.id])
        self.assertEqual(to_lobby.owner_id, self.user_3.id)

        self.assertCountEqual(remaining_lobby.players_ids, [self.user_2.id])
        self.assertEqual(remaining_lobby.owner_id, self.user_2.id)

        fl, tl, rl = models.Lobby.move_player(self.user_2.id, remaining_lobby.owner_id)
        self.assertEqual(fl.owner_id, self.user_2.id)
        self.assertEqual(tl.owner_id, self.user_2.id)
        self.assertIsNone(rl)

        l1 = models.Lobby.get(self.user_1.id)
        self.assertCountEqual(l1.players_ids, [])

        l2 = models.Lobby.get(self.user_2.id)
        self.assertCountEqual(l2.players_ids, [self.user_2.id])

        l3 = models.Lobby.get(self.user_3.id)
        self.assertCountEqual(l3.players_ids, [self.user_3.id, self.user_1.id])

        l1 = models.Lobby.get_by_player_id(self.user_1.id)
        self.assertCountEqual(l1.players_ids, [self.user_3.id, self.user_1.id])

        l2 = models.Lobby.get_by_player_id(self.user_2.id)
        self.assertCountEqual(l2.players_ids, [self.user_2.id])

        l3 = models.Lobby.get_by_player_id(self.user_3.id)
        self.assertCountEqual(l3.players_ids, [self.user_3.id, self.user_1.id])

    def test_move_player_owner_leave_and_delete(self):
        models.Lobby.create(self.user_2.id)
        l1 = models.Lobby.create(self.user_1.id)
        l2 = models.Lobby.create(self.user_3.id)
        l1.update_visibility(visibility='public')
        l2.update_visibility(visibility='public')

        models.Lobby.move_player(self.user_2.id, l1.owner_id)
        _, tl, _ = models.Lobby.move_player(self.user_1.id, self.user_1.id)
        tl.delete()

        lobby = models.Lobby.get_by_player_id(self.user_1.id, fail_silently=True)
        self.assertIsNone(lobby)

    def test_move_player_pre_match(self):
        l1 = models.Lobby.create(owner_id=self.user_1.id)
        l2 = models.Lobby.create(owner_id=self.user_2.id)
        l1.update_visibility(visibility='public')
        l2.update_visibility(visibility='public')

        cache.set(f'{l1.cache_key}:pre_match_id', 1)
        with self.assertRaisesRegex(models.LobbyException, 'while in match'):
            fl, tl, _ = models.Lobby.move_player(self.user_1.id, l2.owner_id)
            self.assertIsNone(fl)
            self.assertIsNone(tl)

        cache.delete(f'{l1.cache_key}:pre_match_id')
        fl, tl, _ = models.Lobby.move_player(self.user_1.id, l2.owner_id)
        self.assertEqual(len(fl.players_ids), 0)
        self.assertEqual(len(tl.players_ids), 2)
        self.assertIsNotNone(fl)
        self.assertIsNotNone(tl)


class LobbyInviteModelTestCase(VerifiedAccountsMixin, TestCase):
    def test_incr_auto_id(self):
        auto_id_key = f'{models.LobbyInvite.Config.CACHE_PREFIX}:auto_id'
        self.assertIsNone(cache.get(auto_id_key))
        models.LobbyInvite.incr_auto_id()
        self.assertIsNotNone(cache.get(auto_id_key))
        self.assertEqual(int(cache.get(auto_id_key)), 1)
        models.LobbyInvite.incr_auto_id()
        self.assertEqual(int(cache.get(auto_id_key)), 2)

    def test_create(self):
        lobby = models.Lobby.create(self.user_1.id)
        self.assertCountEqual(lobby.invites_ids, [])

        i1 = models.LobbyInvite.create(lobby.id, self.user_1.id, self.user_2.id)
        lobby = models.Lobby.get(lobby.owner_id)
        self.assertCountEqual(lobby.invites_ids, [i1.id])

        i2 = models.LobbyInvite.create(lobby.id, self.user_1.id, self.user_3.id)
        lobby = models.Lobby.get(lobby.owner_id)
        self.assertCountEqual(lobby.invites_ids, [i1.id, i2.id])

        models.Lobby.create(self.user_2.id)
        models.Lobby.move_player(self.user_2.id, lobby.owner_id)
        i3 = models.LobbyInvite.create(lobby.id, self.user_2.id, self.user_5.id)
        lobby = models.Lobby.get(lobby.owner_id)
        self.assertCountEqual(lobby.invites_ids, [i1.id, i2.id, i3.id])

    def test_create_outside_lobby(self):
        lobby = models.Lobby.create(self.user_1.id)
        self.assertCountEqual(lobby.invites_ids, [])

        with self.assertRaisesRegex(models.LobbyInviteException, 'another lobby'):
            models.LobbyInvite.create(lobby.id, self.user_2.id, self.user_4.id)

    def test_create_exists(self):
        lobby = models.Lobby.create(self.user_1.id)
        models.Lobby.create(self.user_2.id)
        models.LobbyInvite.create(lobby.id, self.user_1.id, self.user_2.id)
        models.Lobby.move_player(self.user_2.id, lobby.owner_id)

        models.LobbyInvite.create(lobby.id, self.user_1.id, self.user_3.id)
        with self.assertRaisesRegex(models.LobbyInviteException, 'already exists'):
            models.LobbyInvite.create(lobby.id, self.user_2.id, self.user_3.id)

        models.LobbyInvite.create(lobby.id, self.user_2.id, self.user_4.id)

    def test_get(self):
        lobby = models.Lobby.create(self.user_1.id)
        created = models.LobbyInvite.create(lobby.id, self.user_1.id, self.user_2.id)
        invite = models.LobbyInvite.get(created.id)
        self.assertIsNotNone(invite)

    def test_get_by_player_id(self):
        lobby = models.Lobby.create(self.user_1.id)
        created = models.LobbyInvite.create(lobby.id, self.user_1.id, self.user_2.id)
        invites = models.LobbyInvite.get_by_player_id(self.user_1.id, kind='sent')
        self.assertCountEqual(invites, [created])

        lobby = models.Lobby.create(self.user_2.id)
        created = models.LobbyInvite.create(lobby.id, self.user_2.id, self.user_1.id)
        invites = models.LobbyInvite.get_by_player_id(self.user_2.id, kind='sent')
        self.assertCountEqual(invites, [created])

        invites = models.LobbyInvite.get_by_player_id(self.user_2.id, kind='all')
        self.assertEqual(len(invites), 2)

        invites = models.LobbyInvite.get_by_player_id(self.user_1.id, kind='all')
        self.assertEqual(len(invites), 2)


# class PlayerModelTestCase(VerifiedAccountsMixin, TestCase):
#     def setUp(self) -> None:
#         super().setUp()
#         self.user_1.add_session()
#         self.user_2.add_session()

#     @override_settings(
#         PLAYER_DODGES_MIN_TO_RESTRICT=3,
#         PLAYER_DODGES_MULTIPLIER=[1, 2, 5, 10, 20, 40, 60, 90],
#     )
#     def test_restriction_countdown(self):
#         AppSettings.objects.create(
#             kind=AppSettings.BOOLEAN,
#             name='Dodges Restriction',
#             value='1',
#         )
#         lobby = Lobby.create(self.user_1.id)
#         lobby.update_visibility('public')
#         Lobby.create(self.user_2.id)
#         Lobby.move_player(self.user_2.id, lobby.id)

#         self.assertIsNone(lobby.restriction_countdown)
#         handle_dodges(lobby, [self.user_1.id])
#         self.assertIsNone(lobby.restriction_countdown)
#         handle_dodges(lobby, [self.user_1.id])
#         self.assertIsNone(lobby.restriction_countdown)
#         handle_dodges(lobby, [self.user_1.id])
#         restriction = PlayerRestriction.objects.get(user=self.user_2)
#         self.assertEqual(
#             lobby.restriction_countdown,
#             (restriction.end_date - timezone.now()).seconds,
#         )
#         handle_dodges(lobby, [self.user_2.id])
#         handle_dodges(lobby, [self.user_2.id])
#         handle_dodges(lobby, [self.user_2.id])
#         handle_dodges(lobby, [self.user_2.id])
#         restriction = PlayerRestriction.objects.get(user=self.user_1)
#         self.assertEqual(
#             lobby.restriction_countdown,
#             (restriction.end_date - timezone.now()).seconds,
#         )
