from unittest import mock

from model_bakery import baker
from ninja.errors import AuthenticationError, Http404, HttpError

from core.tests import TestCase
from matches.models import Match, MatchPlayer, MatchTeam, Server

from ..api import controller
from ..models import PreMatch, PreMatchConfig
from . import mixins


class MatchControllerTestCase(mixins.TeamsMixin, TestCase):
    @mock.patch('matchmaking.api.controller.cancel_match_after_countdown.apply_async')
    def test_match_player_lock_in(self, mocker):
        match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(match.players_in, 0)

        controller.match_player_lock_in(self.user_1, match.id)
        self.assertEqual(match.players_in, 1)

        with self.assertRaises(Http404):
            controller.match_player_lock_in(self.user_1, 'UNKNOWN_ID')

        with self.assertRaises(AuthenticationError):
            controller.match_player_lock_in(self.user_15, match.id)

        for _ in range(0, 8):
            match.set_player_lock_in()

        self.assertEqual(match.state, PreMatchConfig.STATES.get('pre_start'))
        controller.match_player_lock_in(self.user_10, match.id)
        self.assertEqual(match.state, PreMatchConfig.STATES.get('lock_in'))
        mocker.assert_called_once()

    def test_match_player_lock_in_while_in_match(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(pre_match.players_in, 0)

        with self.assertRaises(HttpError):
            match = baker.make(Match)
            team = baker.make(MatchTeam, match=match)
            baker.make(MatchPlayer, user=self.user_1, team=team)
            controller.match_player_lock_in(self.user_1, match.id)

    @mock.patch('matchmaking.api.controller.pre_match_task.delay')
    def test_match_player_ready(self, mocker):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)

        for _ in range(0, 10):
            pre_match.set_player_lock_in()

        pre_match.start_players_ready_countdown()
        controller.match_player_ready(self.user_1, pre_match.id)
        self.assertEqual(len(pre_match.players_ready), 1)

        with self.assertRaises(Http404):
            controller.match_player_ready(self.user_1, 'UNKNOWN_ID')

        with self.assertRaises(AuthenticationError):
            controller.match_player_ready(self.user_15, pre_match.id)

        for player in pre_match.players[1:9]:
            controller.match_player_ready(player, pre_match.id)

        with self.assertRaises(HttpError):
            controller.match_player_ready(self.user_1, pre_match.id)

        self.assertEqual(pre_match.state, PreMatchConfig.STATES.get('lock_in'))
        controller.match_player_ready(self.user_10, pre_match.id)
        self.assertEqual(pre_match.state, PreMatchConfig.STATES.get('ready'))
        self.assertEqual(mocker.call_count, 10)
        mocker.assert_called_with(pre_match.id)

    def test_match_player_ready_while_in_match(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for _ in range(0, 10):
            pre_match.set_player_lock_in()
        pre_match.start_players_ready_countdown()

        with self.assertRaises(HttpError):
            match = baker.make(Match)
            team = baker.make(MatchTeam, match=match)
            baker.make(MatchPlayer, user=self.user_1, team=team)
            controller.match_player_ready(self.user_1, match.id)

    def test_create_match(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for _ in range(0, 10):
            pre_match.set_player_lock_in()

        pre_match.start_players_ready_countdown()

        for player in pre_match.players[:10]:
            pre_match.set_player_ready(player.id)

        Server.objects.create(ip='123.123.123.123', name='Reload 1', key='key')
        controller.create_match(pre_match)
        match_player_user1 = self.user_1.matchplayer_set.first()
        match_player_user6 = self.user_6.matchplayer_set.first()
        self.assertIsNotNone(match_player_user1)
        self.assertIsNotNone(match_player_user6)
        self.assertEqual(match_player_user1.team.match, match_player_user6.team.match)
