from unittest import mock

from django.utils import timezone

from core.redis import redis_client_instance as cache
from core.tests import TestCase
from lobbies.models import Player

from ..models import PreMatch, PreMatchException, Team, TeamException
from ..tasks import cancel_match_after_countdown
from . import mixins


class PreMatchTasksTestCase(mixins.TeamsMixin, TestCase):
    @mock.patch('pre_matches.tasks.ws_update_user')
    @mock.patch('pre_matches.tasks.ws_create_toast')
    @mock.patch('pre_matches.tasks.ws_friend_update_or_create')
    @mock.patch('pre_matches.tasks.websocket.ws_pre_match_delete')
    def test_cancel_match_after_countdown(
        self,
        mock_pre_match_delete,
        mock_friend_update,
        mock_create_toast,
        mock_update_user,
    ):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        player1 = Player(user_id=pre_match.players[0].id)
        player2 = Player(user_id=pre_match.players[1].id)

        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        pre_match.start_players_ready_countdown()
        pre_match.set_player_ready(player1.user_id)

        past_time = (timezone.now() - timezone.timedelta(seconds=40)).isoformat()
        cache.set(f'{pre_match.cache_key}:ready_time', past_time)

        cancel_match_after_countdown(pre_match.id)

        self.assertEqual(player1.dodges, 0)
        self.assertEqual(player2.dodges, 1)

        mock_calls = [
            mock.call(self.user_1),
            mock.call(self.user_2),
        ]

        mock_pre_match_delete.assert_called_once()
        self.assertEqual(mock_create_toast.call_count, 9)
        mock_friend_update.assert_has_calls(mock_calls)
        mock_update_user.assert_has_calls(mock_calls)

        with self.assertRaises(PreMatchException):
            PreMatch.get_by_id(pre_match.id)

        with self.assertRaises(TeamException):
            Team.get_by_id(self.team1.id, raise_error=True)
            Team.get_by_id(self.team2.id, raise_error=True)

    @mock.patch('pre_matches.tasks.websocket.ws_pre_match_delete')
    def test_cancel_match_after_countdown_multiple_teams(
        self,
        mock_pre_match_delete,
    ):
        pre_match_1 = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match_1.players:
            pre_match_1.set_player_lock_in(player.id)

        pre_match_2 = PreMatch.create(self.team3.id, self.team4.id)
        for player in pre_match_2.players:
            pre_match_2.set_player_lock_in(player.id)

        pre_match_1.start_players_ready_countdown()
        past_time = (timezone.now() - timezone.timedelta(seconds=15)).isoformat()
        cache.set(f'{pre_match_1.cache_key}:ready_time', past_time)

        pre_match_2.start_players_ready_countdown()

        past_time = (timezone.now() - timezone.timedelta(seconds=40)).isoformat()
        cache.set(f'{pre_match_1.cache_key}:ready_time', past_time)
        cancel_match_after_countdown(pre_match_1.id)

        past_time = (timezone.now() - timezone.timedelta(seconds=40)).isoformat()
        cache.set(f'{pre_match_2.cache_key}:ready_time', past_time)
        cancel_match_after_countdown(pre_match_2.id)

        self.assertEqual(mock_pre_match_delete.call_count, 2)
