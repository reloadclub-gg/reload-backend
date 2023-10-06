from unittest import mock

from django.test import override_settings
from django.utils import timezone

from core.redis import redis_client_instance as cache
from core.tests import TestCase
from pre_matches.models import Team
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
