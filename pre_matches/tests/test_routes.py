from core.tests import APIClient, TestCase

from ..models import PreMatch
from . import mixins


class PreMatchRoutesTestCase(mixins.TeamsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.api = APIClient('/api/pre-matches')

    def test_lock_in(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.type_mode[0],
            self.team1.type_mode[1],
        )
        response = self.api.call(
            'post',
            '/lock-in/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(pre_match.players_in), 1)

        self.api.call(
            'post',
            '/lock-in/',
            token=self.user_3.auth.token,
        )
        self.assertEqual(len(pre_match.players_in), 2)

        bad_response = self.api.call(
            'post',
            '/lock-in/',
            token=self.user_14.auth.token,
        )
        self.assertEqual(bad_response.status_code, 404)
        self.assertEqual(len(pre_match.players_in), 2)

    def test_ready(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.type_mode[0],
            self.team1.type_mode[1],
        )
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        response = self.api.call(
            'post',
            '/ready/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(pre_match.players_ready), 1)

        self.api.call(
            'post',
            '/ready/',
            token=self.user_3.auth.token,
        )
        self.assertEqual(len(pre_match.players_ready), 2)

        bad_response = self.api.call(
            'post',
            '/ready/',
            token=self.user_14.auth.token,
        )
        self.assertEqual(bad_response.status_code, 404)
        self.assertEqual(len(pre_match.players_ready), 2)

    def test_detail(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.type_mode[0],
            self.team1.type_mode[1],
        )
        response = self.api.call(
            'get',
            '/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(pre_match.id, response.json().get('id'))
