import time
from threading import Thread
from unittest import mock

from django.test import override_settings
from django.utils import timezone
from ninja.errors import Http404

from accounts.tasks import watch_user_status_change
from core.redis import redis_client_instance as cache
from core.tests import TestCase
from lobbies.api.controller import update_lobby
from lobbies.api.schemas import LobbyUpdateSchema
from lobbies.models import Lobby
from pre_matches.api.controller import set_player_lock_in, set_player_ready
from pre_matches.models import PreMatch, Team, TeamException
from pre_matches.tests.mixins import TeamsMixin

from .. import models, tasks
from . import mixins


class LobbyTasksTestCase(TeamsMixin, TestCase):
    def test_clear_dodges(self):
        player = models.Player.create(self.user_1.id)
        tasks.clear_dodges()
        self.assertEqual(player.dodges, 0)
        today = timezone.now().isoformat()
        two_weeks_ago = (timezone.now() - timezone.timedelta(weeks=2)).isoformat()

        cache.zadd(
            f'{player.cache_key}:dodges',
            {two_weeks_ago: 1680800659.26437},
        )
        tasks.clear_dodges()
        self.assertEqual(player.dodges, 0)

        cache.zadd(
            f'{player.cache_key}:dodges',
            {today: 1680800759.26437},
        )
        tasks.clear_dodges()
        self.assertEqual(player.dodges, 1)


class LobbyMMTasksTestCase(mixins.LobbiesMixin, TestCase):
    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    def test_queue_min_1_player(self):
        self.assertEqual(len(Team.get_all()), 0)
        self.lobby1.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)

        self.lobby2.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    def test_queue_min_2_players(self):
        self.assertEqual(len(Team.get_all()), 0)
        self.lobby1.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)

        self.lobby2.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)

        self.lobby3.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)

        self.lobby4.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('lobbies.tasks.handle_match_found')
    def test_matchmaking(self, mock_match_found):
        t1 = Team.create([self.lobby1.id])
        t2 = Team.create([self.lobby2.id])
        tasks.handle_matchmaking()
        mock_match_found.asser_called_once_with(t1, t2)

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    @mock.patch('lobbies.tasks.handle_match_found')
    def test_matchmaking_not_match(self, mock_match_found):
        Team.create([self.lobby1.id, self.lobby2.id])
        Team.create([self.lobby3.id])
        tasks.handle_matchmaking()
        mock_match_found.assert_not_called()

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_teaming(self, mock_tick):
        t1 = Team.create([self.lobby1.id])
        t2 = Team.create([self.lobby2.id])
        t3 = Team.create([self.lobby3.id])
        self.user_4.account.lobby.start_queue()

        tasks.handle_teaming()

        mock_tick.assert_called_once_with(self.user_4.account.lobby)
        count = sum(
            [
                self.user_4.account.lobby.id in lst
                for lst in [
                    t1.lobbies_ids,
                    t2.lobbies_ids,
                    t3.lobbies_ids,
                ]
            ]
        )

        self.assertEqual(count, 1)

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_teaming_create_team(self, mock_tick):
        Team.create([self.lobby1.id])
        Team.create([self.lobby2.id])
        Team.create([self.lobby3.id])
        self.user_4.account.lobby.start_queue()

        with self.assertRaises(TeamException):
            Team.get_by_lobby_id(self.user_4.account.lobby.id)

        tasks.handle_teaming()
        mock_tick.assert_called_once_with(self.user_4.account.lobby)
        self.assertIsNotNone(Team.get_by_lobby_id(self.user_4.account.lobby.id))

    @override_settings(TEAM_READY_PLAYERS_MIN=5)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_queue_each_lobby(self, mock_tick):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()

        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)
        self.lobby5.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 1)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 0)

        self.lobby6.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)

        self.lobby7.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)

        self.lobby8.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)

        self.lobby9.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)
        self.assertEqual(len(Team.get_all_not_ready()), 1)

        self.lobby10.start_queue()
        tasks.queue()
        self.assertEqual(len(PreMatch.get_all()), 1)
        pm = PreMatch.get_all()[0]
        self.assertIn(Team.get_all()[0], pm.teams)
        self.assertIn(Team.get_all()[1], pm.teams)

    @override_settings(TEAM_READY_PLAYERS_MIN=5)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_queue_composed_lobbies(self, mock_tick):
        self.lobby1.set_public()
        self.lobby5.set_public()
        self.lobby7.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)
        Lobby.move(self.user_4.id, self.lobby1.id)
        Lobby.move(self.user_6.id, self.lobby5.id)
        Lobby.move(self.user_8.id, self.lobby7.id)
        Lobby.move(self.user_9.id, self.lobby7.id)
        Lobby.move(self.user_10.id, self.lobby7.id)

        self.lobby1.start_queue()
        tasks.queue()
        t1 = Team.get_by_lobby_id(self.lobby1.id)
        self.assertIsNotNone(t1)
        self.assertFalse(t1.ready)
        self.assertIn(self.lobby1.id, t1.lobbies_ids)
        self.assertEqual(t1.players_count, self.lobby1.players_count)

        self.lobby5.start_queue()
        tasks.queue()
        t2 = Team.get_by_lobby_id(self.lobby5.id)
        self.assertIsNotNone(t2)
        self.assertFalse(t2.ready)
        self.assertIn(self.lobby5.id, t2.lobbies_ids)
        self.assertEqual(t2.players_count, self.lobby5.players_count)
        self.assertEqual(len(Team.get_all_not_ready()), 2)

        self.lobby7.start_queue()
        tasks.queue()
        t3 = Team.get_by_lobby_id(self.lobby7.id)
        self.assertFalse(t3.ready)
        self.assertIn(self.lobby7.id, t3.lobbies_ids)
        self.assertEqual(t3.players_count, self.lobby7.players_count)
        self.assertEqual(len(Team.get_all_not_ready()), 3)

        self.lobby11.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all_not_ready()), 2)
        self.assertEqual(len(Team.get_all_ready()), 1)

        self.lobby12.start_queue()
        tasks.queue()
        self.assertEqual(len(Team.get_all_not_ready()), 1)
        self.assertIsNotNone(PreMatch.get_by_player_id(self.lobby12.id))
        self.assertEqual(len(PreMatch.get_all()), 1)
        self.assertIn(t1, PreMatch.get_all()[0].teams)
        self.assertIn(t3, PreMatch.get_all()[0].teams)
        self.assertNotIn(t2, PreMatch.get_all()[0].teams)

    @override_settings(TEAM_READY_PLAYERS_MIN=5, FIVEM_MATCH_MOCK_DELAY_CONFIGURE=0)
    @mock.patch(
        'pre_matches.api.controller.tasks.cancel_match_after_countdown.apply_async'
    )
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_queue_someone_quit(self, mock_tick, mock_cancel_match):
        self.lobby1.set_public()
        self.lobby4.set_public()
        self.lobby6.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)
        Lobby.move(self.user_5.id, self.lobby4.id)
        Lobby.move(self.user_7.id, self.lobby6.id)
        Lobby.move(self.user_8.id, self.lobby6.id)
        Lobby.move(self.user_9.id, self.lobby6.id)
        Lobby.move(self.user_10.id, self.lobby6.id)

        self.lobby1.start_queue()
        self.lobby4.start_queue()
        self.lobby6.start_queue()
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

        for player in pm.players:
            set_player_lock_in(player)

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
    def test_handle_teaming_lobby_cancel_queue(self, mock_tick):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        thread = Thread(target=tasks.handle_teaming)
        thread.start()
        time.sleep(0.001)
        update_lobby(
            self.user_2,
            self.lobby2.id,
            LobbyUpdateSchema.from_orm({'cancel_queue': True}),
        )
        thread.join()
        t1 = Team.get_by_lobby_id(self.lobby1.id, fail_silently=True)
        t2 = Team.get_by_lobby_id(self.lobby2.id, fail_silently=True)
        self.assertIsNotNone(t1)
        self.assertIsNone(t2)

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_handle_matchmaking_lobby_cancel_queue(self, mock_tick):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
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

    @override_settings(TEAM_READY_PLAYERS_MIN=5)
    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_mm_balance_teams(self, mock_queue_tick):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        self.lobby1.start_queue()

        tasks.handle_teaming()

        self.lobby3.set_public()
        Lobby.move(self.user_4.id, self.lobby3.id)
        self.lobby3.start_queue()
        tasks.handle_teaming()

        self.lobby5.set_public()
        Lobby.move(self.user_6.id, self.lobby5.id)
        Lobby.move(self.user_7.id, self.lobby5.id)
        self.lobby5.start_queue()
        tasks.handle_teaming()

        # self.assertEqual(len(Team.get_all_ready()), 1)
        # self.assertEqual(len(Team.get_all_not_ready()), 1)
