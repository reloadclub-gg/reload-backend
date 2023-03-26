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
