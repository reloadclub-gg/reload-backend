from unittest import mock

from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from ninja.errors import Http404

from accounts.tasks import watch_user_status_change
from appsettings.models import AppSettings
from core.tests import TestCase
from lobbies.models import Lobby
from pre_matches.api.controller import set_player_ready
from pre_matches.models import PreMatch, Team, TeamException
from pre_matches.tests.mixins import TeamsMixin

from .. import models, tasks
from . import mixins


class LobbyTasksTestCase(TeamsMixin, TestCase):
    @override_settings(PLAYER_DODGES_EXPIRE_TIME=60 * 60 * 24 * 7)  # 1 semana (7 dias)
    def test_clear_dodges(self):
        old_week = timezone.now() - timezone.timedelta(weeks=2)
        yesterday = timezone.now() - timezone.timedelta(days=1)

        models.PlayerDodges(user=self.user_1, count=4).save()
        models.PlayerDodges.objects.filter(user=self.user_1).update(
            last_dodge_date=old_week
        )
        self.assertEqual(self.user_1.playerdodges.count, 4)
        tasks.clear_dodges()
        self.user_1.playerdodges.refresh_from_db()
        self.assertEqual(self.user_1.playerdodges.count, 0)

        models.PlayerDodges(user=self.user_2, count=3).save()
        models.PlayerDodges.objects.filter(user=self.user_2).update(
            last_dodge_date=yesterday
        )
        self.assertEqual(self.user_2.playerdodges.count, 3)
        tasks.clear_dodges()
        self.user_2.playerdodges.refresh_from_db()
        self.assertEqual(self.user_2.playerdodges.count, 3)


class LobbyMMTasksTestCase(mixins.LobbiesMixin, TestCase):
    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    def test_queue_min_1_player(self):
        self.assertEqual(len(Team.get_all()), 0)
        self.lobby1.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)

        self.lobby2.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    def test_queue_min_2_players(self):
        self.assertEqual(len(Team.get_all()), 0)
        self.lobby1.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)

        self.lobby2.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)

        self.lobby3.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)

        self.lobby4.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('lobbies.tasks.handle_match_found')
    def test_matchmaking(self, mock_match_found):
        self.lobby1.update_queue('start')
        self.lobby2.update_queue('start')
        t1 = Team.create([self.lobby1.id])
        t2 = Team.create([self.lobby2.id])
        tasks.handle_matchmaking()
        mock_match_found.asser_called_once_with(t1, t2)

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    @mock.patch('lobbies.tasks.handle_match_found')
    def test_matchmaking_not_match(self, mock_match_found):
        self.lobby1.update_queue('start')
        self.lobby2.update_queue('start')
        self.lobby3.update_queue('start')
        Team.create([self.lobby1.id, self.lobby2.id])
        Team.create([self.lobby3.id])
        tasks.handle_matchmaking()
        mock_match_found.assert_not_called()

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_teaming(self, mock_tick):
        self.lobby1.update_queue('start')
        self.lobby2.update_queue('start')
        self.lobby3.update_queue('start')
        t1 = Team.create([self.lobby1.id])
        t2 = Team.create([self.lobby2.id])
        t3 = Team.create([self.lobby3.id])
        self.lobby4.update_queue('start')
        tasks.handle_teaming()

        all_lobbies = t1.lobbies_ids + t2.lobbies_ids + t3.lobbies_ids
        self.assertEqual(mock_tick.call_count, 4)
        self.assertTrue(self.lobby4.id in all_lobbies)

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_teaming_create_team(self, mock_tick):
        self.lobby1.update_queue('start')
        self.lobby2.update_queue('start')
        self.lobby3.update_queue('start')
        Team.create([self.lobby1.id])
        Team.create([self.lobby2.id])
        Team.create([self.lobby3.id])
        self.user_4.account.lobby.update_queue('start')

        with self.assertRaises(TeamException):
            Team.get_by_lobby_id(self.user_4.account.lobby.id)

        tasks.handle_teaming()
        self.assertEqual(mock_tick.call_count, 4)
        self.assertIsNotNone(Team.get_by_lobby_id(self.user_4.account.lobby.id))

    @override_settings(TEAM_READY_PLAYERS_MIN=5)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_queue_each_lobby(self, mock_tick):
        self.lobby1.update_queue('start')
        self.lobby2.update_queue('start')
        self.lobby3.update_queue('start')
        self.lobby4.update_queue('start')

        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)
        self.lobby5.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 0)

        self.lobby6.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)

        self.lobby7.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)

        self.lobby8.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)

        self.lobby9.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)

        self.lobby10.update_queue('start')
        tasks.queue()
        self.assertEqual(len(PreMatch.get_all()), 1)
        pm = PreMatch.get_all()[0]
        self.assertIn(Team.get_all()[0], pm.teams)
        self.assertIn(Team.get_all()[1], pm.teams)

    @override_settings(TEAM_READY_PLAYERS_MIN=5)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_queue_composed_lobbies(self, mock_tick):
        self.lobby1.update_visibility('public')
        self.lobby5.update_visibility('public')
        self.lobby7.update_visibility('public')
        Lobby.move_player(self.user_2.id, self.lobby1.id)
        Lobby.move_player(self.user_3.id, self.lobby1.id)
        _, tl1, _ = Lobby.move_player(self.user_4.id, self.lobby1.id)
        _, tl5, _ = Lobby.move_player(self.user_6.id, self.lobby5.id)
        Lobby.move_player(self.user_8.id, self.lobby7.id)
        Lobby.move_player(self.user_9.id, self.lobby7.id)
        _, tl7, _ = Lobby.move_player(self.user_10.id, self.lobby7.id)

        tl1.update_queue('start')
        tasks.queue()
        t1 = Team.get_by_lobby_id(tl1.id)
        self.assertIsNotNone(t1)
        self.assertFalse(t1.ready)
        self.assertIn(tl1.id, t1.lobbies_ids)
        self.assertEqual(t1.players_count, len(tl1.players_ids))

        tl5.update_queue('start')
        tasks.queue()
        t2 = Team.get_by_lobby_id(tl5.id)
        self.assertIsNotNone(t2)
        self.assertFalse(t2.ready)
        self.assertIn(tl5.id, t2.lobbies_ids)
        self.assertEqual(t2.players_count, len(tl5.players_ids))
        self.assertEqual(len(Team.get_all_not_ready()), 2)

        tl7.update_queue('start')
        tasks.queue()
        t3 = Team.get_by_lobby_id(tl7.id)
        self.assertFalse(t3.ready)
        self.assertIn(tl7.id, t3.lobbies_ids)
        self.assertEqual(t3.players_count, len(tl7.players_ids))
        self.assertEqual(len(Team.get_all_not_ready()), 3)

        self.lobby11.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all_not_ready()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)

        self.lobby12.update_queue('start')
        tasks.queue()
        self.assertEqual(len(Team.get_all_not_ready()), 1)
        self.assertIsNotNone(PreMatch.get_by_player_id(self.lobby12.id))
        self.assertEqual(len(PreMatch.get_all()), 1)
        self.assertIn(t1, PreMatch.get_all()[0].teams)
        self.assertIn(t3, PreMatch.get_all()[0].teams)
        self.assertNotIn(t2, PreMatch.get_all()[0].teams)

    @override_settings(TEAM_READY_PLAYERS_MIN=5, FIVEM_MATCH_MOCK_DELAY_CONFIGURE=0)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_queue_someone_quit(self, mock_tick):
        self.lobby1.update_visibility('public')
        self.lobby4.update_visibility('public')
        self.lobby6.update_visibility('public')
        Lobby.move_player(self.user_2.id, self.lobby1.id)
        Lobby.move_player(self.user_3.id, self.lobby1.id)
        Lobby.move_player(self.user_5.id, self.lobby4.id)
        Lobby.move_player(self.user_7.id, self.lobby6.id)
        Lobby.move_player(self.user_8.id, self.lobby6.id)
        Lobby.move_player(self.user_9.id, self.lobby6.id)
        Lobby.move_player(self.user_10.id, self.lobby6.id)

        self.lobby1.update_queue('start')
        self.lobby4.update_queue('start')
        self.lobby6.update_queue('start')
        tasks.queue()
        t1_l1 = Team.get_by_lobby_id(self.lobby1.id, fail_silently=True)
        t1_l2 = Team.get_by_lobby_id(self.lobby4.id, fail_silently=True)
        t2 = Team.get_by_lobby_id(self.lobby6.id, fail_silently=True)
        self.assertEqual(t1_l1, t1_l2)
        self.assertIsNotNone(t1_l1)
        self.assertIsNotNone(t1_l2)
        self.assertIsNotNone(t2)

        pm = PreMatch.get_by_player_id(self.user_2.id)
        self.assertIsNotNone(pm)
        left_out = pm.players[-1:][0]

        for player in pm.players[:-1]:
            set_player_ready(player)

        pm.players_ready[0].auth.expire_session(0)
        self.assertIsNone(pm.players_ready[0].auth.sessions)
        watch_user_status_change(pm.players_ready[0].id)
        with self.assertRaises(Http404):
            set_player_ready(left_out)

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_matchmaking_lobby_cancel_queue(self, mock_tick):
        self.lobby1.update_queue('start')
        self.lobby2.update_queue('start')
        tasks.handle_teaming()
        t1 = Team.get_by_lobby_id(self.lobby1.id, fail_silently=True)
        t2 = Team.get_by_lobby_id(self.lobby2.id, fail_silently=True)
        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)

        tasks.handle_matchmaking()
        self.user_2.auth.expire_session(0)
        watch_user_status_change(self.user_2.id)
        t1 = Team.get_by_lobby_id(self.lobby1.id, fail_silently=True)
        t2 = Team.get_by_lobby_id(self.lobby2.id, fail_silently=True)
        self.assertIsNone(t1)
        self.assertIsNone(t2)

        tasks.handle_teaming()
        t1 = Team.get_by_lobby_id(self.lobby1.id, fail_silently=True)
        t2 = Team.get_by_lobby_id(self.lobby2.id, fail_silently=True)
        self.assertIsNone(t1)
        self.assertIsNone(t2)

    @override_settings(
        PLAYER_DODGES_MIN_TO_RESTRICT=3,
        PLAYER_DODGES_MULTIPLIER=[1, 2, 5, 10, 20, 40, 60, 90],
    )
    def test_handle_dodges(self):
        AppSettings.objects.create(
            kind=AppSettings.BOOLEAN,
            name='Dodges Restriction',
            value='1',
        )
        self.assertEqual(models.PlayerDodges.objects.all().count(), 0)
        tasks.handle_dodges(self.user_1.account.lobby, [])
        self.assertEqual(models.PlayerDodges.objects.all().count(), 1)
        player_dodges = models.PlayerDodges.objects.get(user=self.user_1)
        self.assertEqual(player_dodges.count, 1)

        tasks.handle_dodges(self.user_1.account.lobby, [])
        self.assertEqual(models.PlayerDodges.objects.all().count(), 1)
        player_dodges = models.PlayerDodges.objects.get(user=self.user_1)
        self.assertEqual(player_dodges.count, 2)

        self.user_1.account.lobby.update_visibility('public')
        Lobby.move_player(self.user_2.id, self.user_1.account.lobby.id)
        self.assertEqual(models.PlayerRestriction.objects.all().count(), 0)
        tasks.handle_dodges(self.user_1.account.lobby, [self.user_2.id])
        self.assertEqual(models.PlayerDodges.objects.all().count(), 1)
        player_dodges = models.PlayerDodges.objects.get(user=self.user_1)
        self.assertEqual(player_dodges.count, 3)

        self.assertEqual(models.PlayerRestriction.objects.all().count(), 1)

        dodges_to_restrict = settings.PLAYER_DODGES_MIN_TO_RESTRICT
        dodges_multipliers = settings.PLAYER_DODGES_MULTIPLIER
        factor_idx = player_dodges.count - dodges_to_restrict
        if factor_idx > len(dodges_multipliers):
            factor_idx = len(dodges_multipliers) - 1
        factor = dodges_multipliers[factor_idx]
        lock_minutes = player_dodges.count * factor
        player_restriction = models.PlayerRestriction.objects.get(user=self.user_1)
        self.assertEqual(
            player_restriction.end_date.minute,
            (
                player_restriction.start_date + timezone.timedelta(minutes=lock_minutes)
            ).minute,
        )

        tasks.handle_dodges(self.user_1.account.lobby, [self.user_1.id])
        self.assertEqual(models.PlayerDodges.objects.all().count(), 2)
        player_dodges = models.PlayerDodges.objects.get(user=self.user_1)
        self.assertEqual(player_dodges.count, 3)
        player_dodges = models.PlayerDodges.objects.get(user=self.user_2)
        self.assertEqual(player_dodges.count, 1)
