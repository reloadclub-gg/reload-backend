from model_bakery import baker

from appsettings.models import AppSettings
from core.tests import TestCase
from matches.models import Match, MatchPlayer, Server
from matchmaking.tests import mixins


class MatchesModelsTestCase(mixins.TeamsMixin, TestCase):
    def test_server_model(self):
        server = baker.make(Server)
        AppSettings.set_int('Matches Limit', 2)
        AppSettings.set_int('Matches Limit Gap', 1)

        baker.make(Match, server=server)
        self.assertTrue(server.is_almost_full)
        self.assertIsNotNone(Server.get_idle())

        baker.make(Match, server=server)
        self.assertTrue(server.is_full)
        self.assertIsNone(Server.get_idle())

    def test_match_model(self):
        server = baker.make(Server)
        match = baker.make(Match, server=server)
        team1 = match.matchteam_set.create(name=self.team1.name)
        team2 = match.matchteam_set.create(name=self.team2.name)
        self.assertIsNone(match.winner)

        team1.score = 8
        team1.save()
        team2.score = 9
        team2.save()

        self.assertEqual(match.rounds, 17)
        self.assertEqual(match.winner, team2)

    def test_match_player_model(self):
        server = baker.make(Server)
        match = baker.make(Match, server=server)
        team1 = match.matchteam_set.create(name=self.team1.name)
        team2 = match.matchteam_set.create(name=self.team2.name)
        player = baker.make(MatchPlayer, user=self.user_1, team=team1)

        team1.score = 8
        team1.save()
        team2.score = 9
        team2.save()
        self.assertEqual(match.rounds, player.rounds_played)

        player.afk = 3
        player.save()
        self.assertEqual(player.rounds_played, match.rounds - player.afk)


class MatchesMatchPlayerModelTestCase(mixins.TeamsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.server = baker.make(Server)
        self.match = baker.make(Match, server=self.server, status=Match.Status.FINISHED)
        self.team1 = self.match.matchteam_set.create(name=self.team1.name, score=10)
        self.team2 = self.match.matchteam_set.create(name=self.team2.name, score=8)
        self.match

    def test_points_earned(self):
        player = baker.make(
            MatchPlayer,
            team=self.team1,
            kills=25,
            deaths=9,
            assists=6,
            plants=3,
            defuses=4,
        )
        self.assertEqual(player.points_earned, 30)
        player.team = self.team2
        player.save()
        self.assertEqual(player.points_earned, -10)

        player = baker.make(
            MatchPlayer,
            team=self.team1,
            kills=13,
            deaths=10,
            assists=3,
            plants=2,
            defuses=3,
        )
        self.assertEqual(player.points_earned, 21)
        player.team = self.team2
        player.save()
        self.assertEqual(player.points_earned, -14)

        player = baker.make(
            MatchPlayer,
            team=self.team1,
            kills=8,
            deaths=13,
            assists=2,
            plants=2,
            defuses=1,
        )
        self.assertEqual(player.points_earned, 10)
        player.team = self.team2
        player.save()
        self.assertEqual(player.points_earned, -20)

        player = baker.make(
            MatchPlayer,
            team=self.team1,
            kills=13,
            deaths=10,
            assists=3,
            plants=2,
            defuses=3,
            afk=3,
        )
        self.assertEqual(player.points_earned, 12)
        player.team = self.team2
        player.save()
        self.assertEqual(player.points_earned, -23)