from model_bakery import baker

from appsettings.models import AppSettings
from core.tests import TestCase
from matches.models import Match, MatchPlayer, MatchPlayerStats, Server
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
        self.assertEqual(match.rounds, player.stats.rounds_played)

        player.stats.afk = 3
        player.stats.save()
        self.assertEqual(player.stats.rounds_played, match.rounds - player.stats.afk)


class MatchesMatchPlayerModelTestCase(mixins.TeamsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.server = baker.make(Server)
        self.match = baker.make(Match, server=self.server, status=Match.Status.FINISHED)
        self.team1 = self.match.matchteam_set.create(name=self.team1.name, score=10)
        self.team2 = self.match.matchteam_set.create(name=self.team2.name, score=8)

    def test_points_earned(self):
        self.user_1.account.level = 1
        self.user_1.account.save()
        player = baker.make(
            MatchPlayer,
            team=self.team1,
            user=self.user_1,
        )
        MatchPlayerStats.objects.filter(player=player).update(
            kills=25,
            deaths=9,
            assists=6,
            plants=3,
            defuses=4,
        )
        player.refresh_from_db()
        self.assertEqual(player.points_earned, 30)
        player.team = self.team2
        player.save()
        self.assertEqual(player.points_earned, -10)

        self.user_2.account.level = 1
        self.user_2.account.save()
        player = baker.make(
            MatchPlayer,
            team=self.team1,
            user=self.user_2,
        )
        MatchPlayerStats.objects.filter(player=player).update(
            kills=13,
            deaths=10,
            assists=3,
            plants=2,
            defuses=3,
        )
        player.refresh_from_db()
        self.assertEqual(player.points_earned, 21)
        player.team = self.team2
        player.save()
        self.assertEqual(player.points_earned, -14)

        self.user_3.account.level = 1
        self.user_3.account.save()
        player = baker.make(
            MatchPlayer,
            team=self.team1,
            user=self.user_3,
        )
        MatchPlayerStats.objects.filter(player=player).update(
            kills=8,
            deaths=13,
            assists=2,
            plants=2,
            defuses=1,
        )
        player.refresh_from_db()
        self.assertEqual(player.points_earned, 10)
        player.team = self.team2
        player.save()
        self.assertEqual(player.points_earned, -20)

        self.user_4.account.level = 1
        self.user_4.account.save()
        player = baker.make(
            MatchPlayer,
            team=self.team1,
            user=self.user_4,
        )
        MatchPlayerStats.objects.filter(player=player).update(
            kills=13,
            deaths=10,
            assists=3,
            plants=2,
            defuses=3,
            afk=3,
        )
        player.refresh_from_db()
        self.assertEqual(player.points_earned, 12)
        player.team = self.team2
        player.save()
        self.assertEqual(player.points_earned, -23)

        self.user_5.account.level = 0
        self.user_5.account.save()
        player = baker.make(
            MatchPlayer,
            team=self.team2,
            user=self.user_5,
        )
        MatchPlayerStats.objects.filter(player=player).update(
            kills=7,
            deaths=10,
            assists=3,
            plants=2,
            defuses=1,
        )
        player.refresh_from_db()
        self.assertEqual(player.points_earned, 0)

        player = baker.make(
            MatchPlayer,
            team=self.team1,
            user=self.user_6,
        )
        MatchPlayerStats.objects.filter(player=player).update(
            kills=25,
            deaths=9,
            assists=6,
            plants=3,
            defuses=4,
        )
        player.refresh_from_db()
        self.assertEqual(player.points_earned, 30)
