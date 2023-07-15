from unittest import mock

from ninja.errors import Http404, HttpError

from core.tests import TestCase
from matches.models import Server

from ..api import controller
from ..models import PreMatch, PreMatchException, Team, TeamException
from . import mixins


class PreMatchControllerTestCase(mixins.TeamsMixin, TestCase):
    @mock.patch('pre_matches.api.controller.ws_update_user')
    @mock.patch('pre_matches.api.controller.ws_match_create')
    def test_handle_create_match(
        self,
        mock_match_create,
        mock_update_user,
    ):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        pre_match.start_players_ready_countdown()

        for player in pre_match.players[:10]:
            pre_match.set_player_ready(player.id)

        Server.objects.create(ip='123.123.123.123', name='Reload 1')
        match = controller.handle_create_match(pre_match)
        match_player_user1 = self.user_1.matchplayer_set.first()
        match_player_user6 = self.user_6.matchplayer_set.first()
        self.assertIsNotNone(match_player_user1)
        self.assertIsNotNone(match_player_user6)
        self.assertEqual(match_player_user1.team.match, match_player_user6.team.match)

        mock_match_create.assert_called_once_with(match)
        self.assertEqual(mock_update_user.call_count, 10)

    @mock.patch('pre_matches.api.controller.ws_update_user')
    @mock.patch('pre_matches.api.controller.ws_match_create')
    def test_handle_create_match_no_server_available(
        self,
        mock_match_create,
        mock_update_user,
    ):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        pre_match.start_players_ready_countdown()

        for player in pre_match.players[:10]:
            pre_match.set_player_ready(player.id)

        match = controller.handle_create_match(pre_match)
        self.assertIsNone(match)

        mock_match_create.assert_not_called()
        mock_update_user.assert_not_called()

    @mock.patch('pre_matches.api.controller.ws_friend_update_or_create')
    @mock.patch('pre_matches.api.controller.ws_update_user')
    @mock.patch('pre_matches.api.controller.websocket.ws_pre_match_delete')
    @mock.patch('pre_matches.api.controller.ws_create_toast')
    def test_handle_cancel_match(
        self,
        mock_create_toast,
        mock_pre_match_delete,
        mock_update_user,
        mock_friend_update,
    ):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        pre_match.start_players_ready_countdown()

        for player in pre_match.players[:10]:
            pre_match.set_player_ready(player.id)

        controller.handle_cancel_match(pre_match)

        mock_calls = [
            mock.call(self.user_1),
            mock.call(self.user_2),
        ]

        mock_pre_match_delete.assert_called_once()
        self.assertEqual(mock_create_toast.call_count, 10)
        mock_friend_update.assert_has_calls(mock_calls)
        mock_update_user.assert_has_calls(mock_calls)

        with self.assertRaises(PreMatchException):
            PreMatch.get_by_id(pre_match.id)

        with self.assertRaises(TeamException):
            Team.get_by_id(self.team1.id)
            Team.get_by_id(self.team2.id)

    def test_handle_pre_match_checks(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        user = controller.handle_pre_match_checks(self.user_1, 'error')
        self.assertIsNotNone(user)
        self.assertTrue(user in pre_match.players)

    def test_handle_pre_match_checks_match_fail(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        Server.objects.create(ip='123.123.123.123', name='Reload 1')
        controller.handle_create_match(pre_match)

        with self.assertRaises(HttpError):
            controller.handle_pre_match_checks(self.user_1, 'error')

    def test_handle_pre_match_checks_pre_match_fail(self):
        with self.assertRaises(Http404):
            controller.handle_pre_match_checks(self.user_1, 'error')

    def test_get_pre_match(self):
        created = PreMatch.create(self.team1.id, self.team2.id)
        pre_match = controller.get_pre_match(self.user_1)
        self.assertEqual(created.id, pre_match.id)

    def test_get_pre_match_none(self):
        pre_match = controller.get_pre_match(self.user_1)
        self.assertIsNone(pre_match)

    def test_set_player_lock_in(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(len(pre_match.players_in), 0)
        controller.set_player_lock_in(self.user_1)
        self.assertEqual(len(pre_match.players_in), 1)

        controller.set_player_lock_in(self.user_2)
        self.assertEqual(len(pre_match.players_in), 2)

        with self.assertRaises(HttpError):
            controller.set_player_lock_in(self.user_2)

        self.assertEqual(len(pre_match.players_in), 2)

    @mock.patch('pre_matches.api.controller.websocket.ws_pre_match_update')
    @mock.patch(
        'pre_matches.api.controller.tasks.cancel_match_after_countdown.apply_async'
    )
    def test_set_player_lock_in_ready(
        self,
        mock_cancel_match_task,
        mock_pre_match_update,
    ):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match.players[:-1]:
            pre_match.set_player_lock_in(player.id)

        self.assertIsNone(pre_match.countdown)

        controller.set_player_lock_in(pre_match.players[-1:][0])
        self.assertIsNotNone(pre_match.countdown)
        mock_pre_match_update.assert_called_once()
        mock_cancel_match_task.assert_called_once()

    @mock.patch('pre_matches.api.controller.websocket.ws_pre_match_update')
    def test_set_player_ready(self, mock_pre_match_update):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        pre_match.start_players_ready_countdown()

        controller.set_player_ready(self.user_1)
        self.assertTrue(self.user_1 in pre_match.players_ready)
        mock_pre_match_update.assert_called_once()

        with self.assertRaises(HttpError):
            controller.set_player_ready(self.user_1)

    def test_set_player_ready_create_match(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        Server.objects.create(ip='123.123.123.123', name='Reload 1')
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        pre_match.start_players_ready_countdown()

        for player in pre_match.players[:-1]:
            pre_match.set_player_ready(player.id)

        self.assertIsNone(self.user_1.account.match)

        controller.set_player_ready(pre_match.players[-1:][0])
        self.assertIsNotNone(self.user_1.account.match)
