from django.core.exceptions import ValidationError
from model_bakery import baker

from appsettings.models import AppSettings
from appsettings.services import player_max_losing_level_points
from core.tests import TestCase
from matches.models import Match, MatchPlayer, MatchPlayerStats, Server
from pre_matches.tests.mixins import TeamsMixin


class MatchesServerModelTestCase(TeamsMixin, TestCase):
    def test_server_model(self):
        server = baker.make(Server)
        matches_limit = AppSettings.objects.get(name='Matches Limit')
        matches_limit_gap = AppSettings.objects.get(name='Matches Limit Gap')

        matches_limit.value = '2'
        matches_limit.save()

        matches_limit_gap.value = '1'
        matches_limit_gap.save()

        baker.make(Match, server=server, status=Match.Status.FINISHED)
        self.assertFalse(server.is_almost_full)
        self.assertIsNotNone(Server.get_idle())

        baker.make(Match, server=server, status=Match.Status.RUNNING)
        self.assertTrue(server.is_almost_full)
        self.assertIsNotNone(Server.get_idle())

        baker.make(Match, server=server, status=Match.Status.RUNNING)
        self.assertTrue(server.is_full)
        self.assertIsNone(Server.get_idle())


class MatchesMatchModelTestCase(TeamsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.server = baker.make(Server)
        self.match = baker.make(Match, server=self.server)
        self.team1 = self.match.matchteam_set.create(name=self.team1.name)
        self.team2 = self.match.matchteam_set.create(name=self.team2.name)

    def test_teams(self):
        self.assertCountEqual(self.match.teams, [self.team1, self.team2])
        self.assertEqual(self.match.team_a, self.match.teams[0], self.team1)
        self.assertEqual(self.match.team_b, self.match.teams[1], self.team2)

    def test_rounds(self):
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 9
        self.team2.save()

        self.assertEqual(self.match.rounds, 17)

    def test_winner(self):
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 10
        self.team2.save()
        self.assertEqual(self.match.winner, self.team2)

    def test_players(self):
        baker.make(MatchPlayer, team=self.team1, user=self.user_1)
        self.assertEqual(
            list(self.match.players),
            list(self.team1.players) + list(self.team2.players),
        )

    def test_finish(self):
        baker.make(MatchPlayer, team=self.team1, user=self.user_1)
        self.assertEqual(self.match.status, Match.Status.LOADING)
        self.assertIsNone(self.match.end_date)
        self.assertEqual(self.user_1.account.level, 0)
        self.assertEqual(self.user_1.account.level_points, 0)

        with self.assertRaises(ValidationError):
            self.match.finish()

        self.match.status = Match.Status.RUNNING
        self.match.save()

        self.match.finish()
        self.assertEqual(self.match.status, Match.Status.FINISHED)
        self.assertIsNotNone(self.match.end_date)
        self.assertEqual(self.user_1.account.level, 0)
        self.assertEqual(
            self.user_1.account.level_points, self.match.players[0].points_earned
        )

    def test_warmup(self):
        self.assertEqual(self.match.status, Match.Status.LOADING)
        self.match.warmup()
        self.assertEqual(self.match.status, Match.Status.WARMUP)

    def test_start(self):
        self.match.warmup()
        self.assertIsNone(self.match.start_date)
        self.match.start()
        self.assertEqual(self.match.status, Match.Status.RUNNING)
        self.assertIsNotNone(self.match.start_date)

    def test_cancel(self):
        self.match.cancel()
        self.assertEqual(self.match.status, Match.Status.CANCELLED)

        with self.assertRaises(ValidationError):
            self.match.cancel()

        self.match.status = Match.Status.FINISHED
        self.match.save()

        with self.assertRaises(ValidationError):
            self.match.cancel()


class MatchesMatchPlayerModelTestCase(TeamsMixin, TestCase):
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

        self.user_7.account.level = 1
        self.user_7.account.save()
        player = baker.make(
            MatchPlayer,
            team=self.team2,
            user=self.user_7,
        )
        MatchPlayerStats.objects.filter(player=player).update(
            kills=0,
            deaths=4,
            assists=0,
            plants=0,
            defuses=0,
            afk=14,
        )
        player.refresh_from_db()
        self.assertEqual(player.points_earned, player_max_losing_level_points())


class MatchesMatchPlayerStatsModelTestCase(TeamsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.server = baker.make(Server)
        self.match = baker.make(Match, server=self.server)
        self.team1 = self.match.matchteam_set.create(name=self.team1.name)
        self.team2 = self.match.matchteam_set.create(name=self.team2.name)

    def test_rounds_played(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)

        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.rounds_played, self.match.rounds)

        player.stats.afk = 3
        player.stats.save()
        self.assertEqual(
            player.stats.rounds_played, self.match.rounds - player.stats.afk
        )

    def test_clutches(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        player.stats.clutch_v1 = 5
        player.stats.clutch_v2 = 3
        player.stats.clutch_v3 = 1
        player.stats.save()

        self.assertEqual(player.stats.clutches, 9)

    def test_shots_hit(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        player.stats.head_shots = 5
        player.stats.chest_shots = 3
        player.stats.other_shots = 1
        player.stats.save()

        self.assertEqual(player.stats.shots_hit, 9)

    def test_frag(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        player.stats.kills = 5
        player.stats.deaths = 1
        player.stats.assists = 3
        player.stats.save()

        self.assertEqual(player.stats.frag, '5/1/3')

    def test_adr(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.adr, 0.0)

        player.stats.damage = 350
        player.stats.save()
        self.assertEqual(player.stats.adr, 15.22)

    def test_kdr(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.kdr, 0.0)

        player.stats.kills = 5
        player.stats.save()

        self.assertEqual(player.stats.kdr, 5.0)

        player.stats.deaths = 2
        player.stats.save()
        self.assertEqual(player.stats.kdr, 2.5)

    def test_kda(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.kda, 0.0)

        player.stats.kills = 5
        player.stats.save()

        self.assertEqual(player.stats.kda, 5.0)

        player.stats.deaths = 2
        player.stats.save()
        self.assertEqual(player.stats.kda, 2.5)

        player.stats.assists = 3
        player.stats.save()
        self.assertEqual(player.stats.kda, 4.0)

    def test_ahk(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.ahk, 0.0)

        player.stats.hs_kills = 5
        player.stats.shots_fired = 10
        player.stats.save()

        self.assertEqual(player.stats.ahk, 0.5)

    def test_ahr(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.ahr, 0.0)

        player.stats.head_shots = 7
        player.stats.save()

        self.assertEqual(player.stats.ahr, 0.3)

    def test_accuracy(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.accuracy, 0.0)

        player.stats.shots_fired = 40
        player.stats.head_shots = 2
        player.stats.chest_shots = 10
        player.stats.other_shots = 8
        player.stats.save()

        self.assertEqual(player.stats.accuracy, 50)

    def test_head_accuracy(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.head_accuracy, 0.0)

        player.stats.head_shots = 2
        player.stats.chest_shots = 10
        player.stats.other_shots = 8
        player.stats.save()

        self.assertEqual(player.stats.head_accuracy, 10)

    def test_chest_accuracy(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.chest_accuracy, 0.0)

        player.stats.head_shots = 2
        player.stats.chest_shots = 10
        player.stats.other_shots = 8
        player.stats.save()

        self.assertEqual(player.stats.chest_accuracy, 50)

    def test_others_accuracy(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.others_accuracy, 0.0)

        player.stats.head_shots = 2
        player.stats.chest_shots = 10
        player.stats.other_shots = 8
        player.stats.save()

        self.assertEqual(player.stats.others_accuracy, 40)

    def test_hsk(self):
        player = baker.make(MatchPlayer, user=self.user_1, team=self.team1)
        self.team1.score = 8
        self.team1.save()
        self.team2.score = 15
        self.team2.save()
        self.assertEqual(player.stats.hsk, 0.0)

        player.stats.hs_kills = 2
        player.stats.kills = 10
        player.stats.save()

        self.assertEqual(player.stats.hsk, 20)
