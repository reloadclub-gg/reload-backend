from unittest import mock

from django.utils import timezone

from core.redis import RedisClient
from core.tests import TestCase
from lobbies.models import Player

from ..models import PreMatch, PreMatchException, Team, TeamException
from ..tasks import cancel_match_after_countdown
from . import mixins

cache = RedisClient()


class PreMatchTasksTestCase(mixins.TeamsMixin, TestCase):
    @mock.patch('pre_matches.tasks.ws_update_user')
    @mock.patch('pre_matches.tasks.ws_create_toast')
    @mock.patch('pre_matches.tasks.ws_friend_update_or_create')
    @mock.patch('pre_matches.tasks.ws_update_lobby')
    @mock.patch('pre_matches.tasks.websocket.ws_pre_match_delete')
    def test_cancel_match_after_countdown(
        self,
        mock_pre_match_delete,
        mock_update_lobby,
        mock_friend_update,
        mock_create_toast,
        mock_update_user,
    ):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        player1 = Player(user_id=pre_match.players[0].id)
        player2 = Player(user_id=pre_match.players[1].id)

        for _ in range(0, PreMatch.Config.READY_PLAYERS_MIN):
            pre_match.set_player_lock_in()

        pre_match.start_players_ready_countdown()
        pre_match.set_player_ready(player1.user_id)

        past_time = (timezone.now() - timezone.timedelta(seconds=32)).isoformat()
        cache.set(f'{pre_match.cache_key}:ready_time', past_time)

        cancel_match_after_countdown(pre_match.id)

        self.assertEqual(player1.dodges, 0)
        self.assertEqual(player2.dodges, 1)

        mock_calls = [
            mock.call(self.user_1),
            mock.call(self.user_2),
        ]

        mock_pre_match_delete.assert_called_once()
        mock_update_lobby.assert_called_once_with(self.user_1.account.lobby)
        self.assertEqual(mock_create_toast.call_count, 9)
        mock_friend_update.assert_has_calls(mock_calls)
        mock_update_user.assert_has_calls(mock_calls)

        with self.assertRaises(PreMatchException):
            PreMatch.get_by_id(pre_match.id)

        with self.assertRaises(TeamException):
            Team.get_by_id(self.team1.id)
            Team.get_by_id(self.team2.id)
