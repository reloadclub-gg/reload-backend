from unittest import mock

from django.utils import timezone

from core.redis import RedisClient
from core.tests import TestCase

from ..models import (
    Player,
    PreMatch,
    PreMatchConfig,
    PreMatchException,
    Team,
    TeamException,
)
from ..tasks import cancel_match_after_countdown
from . import mixins

cache = RedisClient()


class MMTasksTestCase(mixins.TeamsMixin, TestCase):
    @mock.patch('websocket.controller.match_cancel_warn')
    @mock.patch('websocket.controller.restart_queue')
    @mock.patch('websocket.controller.match_cancel')
    def test_cancel_match_after_countdown(self, mock_cancel, mock_queue, mock_warn):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        player1 = Player(user_id=pre_match.players[0].id)
        player2 = Player(user_id=pre_match.players[1].id)

        for _ in range(0, PreMatchConfig.READY_PLAYERS_MIN):
            pre_match.set_player_lock_in()

        pre_match.start_players_ready_countdown()
        pre_match.set_player_ready(player1.user_id)

        past_time = (timezone.now() - timezone.timedelta(seconds=32)).isoformat()
        cache.set(f'{pre_match.cache_key}:ready_time', past_time)

        cancel_match_after_countdown(pre_match.id)

        self.assertEqual(player1.dodges, 0)
        self.assertEqual(player2.dodges, 1)

        with self.assertRaises(PreMatchException):
            PreMatch.get_by_id(pre_match.id)

        with self.assertRaises(TeamException):
            Team.get_by_id(self.team1.id)
            Team.get_by_id(self.team2.id)
