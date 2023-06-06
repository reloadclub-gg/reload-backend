from core.tests import APIClient, TestCase

from ..models import PreMatch
from . import mixins


class MatchAPITestCase(mixins.TeamsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.api = APIClient('/api/mm')

    def test_match_player_lock_in(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        response = self.api.call(
            'patch',
            f'/match/{match.id}/player-lock-in/',
            token=self.user_1.auth.token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(match.players_in, 1)

        self.api.call(
            'patch',
            f'/match/{match.id}/player-lock-in/',
            token=self.user_3.auth.token,
        )
        self.assertEqual(match.players_in, 2)

        bad_response = self.api.call(
            'patch',
            f'/match/{match.id}/player-lock-in/',
            token=self.user_14.auth.token,
        )
        self.assertEqual(bad_response.status_code, 401)
        self.assertEqual(match.players_in, 2)

        bad_response = self.api.call(
            'patch',
            '/match/UNKNOWN_ID/player-lock-in/',
            token=self.user_14.auth.token,
        )
        self.assertEqual(bad_response.status_code, 404)
        self.assertEqual(match.players_in, 2)
