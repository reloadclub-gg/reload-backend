from unittest import mock

from django.utils import timezone
from model_bakery import baker
from ninja.errors import Http404

from core.tests import TestCase
from pre_matches.tests.mixins import TeamsMixin

from .. import models
from ..api import controller, schemas


class MatchesControllerTestCase(TeamsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.server = baker.make(models.Server)
        self.match = baker.make(
            models.Match,
            server=self.server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        self.match.matchteam_set.create(name=self.team1.name, score=10)
        self.match.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=self.match.team_a, user=self.user_1)
        baker.make(models.MatchPlayer, team=self.match.team_b, user=self.user_2)

    def test_get_user_matches(self):
        match2 = baker.make(
            models.Match,
            server=self.server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match2.matchteam_set.create(name=self.team1.name, score=10)
        match2.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=team1, user=self.user_1)

        results = controller.get_user_matches(self.user_1)
        self.assertEqual(len(results), 2)
        self.assertTrue(self.match in results)
        self.assertTrue(match2 in results)

        match = baker.make(
            models.Match,
            server=self.server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10)
        match.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=team1, user=self.user_2)

        results = controller.get_user_matches(self.user_1, self.user_2.id)
        self.assertEqual(len(results), 2)
        self.assertTrue(match in results)

    def test_handle_update_players_stats(self):
        payload = [
            schemas.MatchUpdatePlayerStats.from_orm(
                {
                    "steamid": self.user_1.account.steamid,
                    "kills": 2,
                    "headshot_kills": 1,
                    "deaths": 1,
                    "assists": 1,
                    "health": 0,
                    "damage": 345,
                    "shots_fired": 66,
                    "head_shots": 1,
                    "chest_shots": 45,
                    "other_shots": 20,
                    "kill_weapons": ['weapon_app_pistol'],
                    "defuse": False,
                    "plant": True,
                    "firstkill": False,
                }
            )
        ]

        player_stats = models.MatchPlayerStats.objects.get(
            player__user=self.user_1,
            player__team__match=self.match,
        )

        self.assertEqual(player_stats.kills, 0)
        self.assertEqual(player_stats.hs_kills, 0)
        self.assertEqual(player_stats.deaths, 0)
        self.assertEqual(player_stats.assists, 0)
        self.assertEqual(player_stats.damage, 0)
        self.assertEqual(player_stats.shots_fired, 0)
        self.assertEqual(player_stats.head_shots, 0)
        self.assertEqual(player_stats.chest_shots, 0)
        self.assertEqual(player_stats.other_shots, 0)
        self.assertEqual(player_stats.defuses, 0)
        self.assertEqual(player_stats.plants, 0)
        self.assertEqual(player_stats.firstkills, 0)

        controller.handle_update_players_stats(payload, self.match)
        player_stats.refresh_from_db()

        self.assertEqual(player_stats.kills, 2)
        self.assertEqual(player_stats.hs_kills, 1)
        self.assertEqual(player_stats.deaths, 1)
        self.assertEqual(player_stats.assists, 1)
        self.assertEqual(player_stats.damage, 345)
        self.assertEqual(player_stats.shots_fired, 66)
        self.assertEqual(player_stats.head_shots, 1)
        self.assertEqual(player_stats.chest_shots, 45)
        self.assertEqual(player_stats.other_shots, 20)
        self.assertEqual(player_stats.defuses, 0)
        self.assertEqual(player_stats.plants, 1)
        self.assertEqual(player_stats.firstkills, 0)

        payload = [
            schemas.MatchUpdatePlayerStats.from_orm(
                {
                    "steamid": self.user_1.account.steamid,
                    "kills": 2,
                    "headshot_kills": 1,
                    "deaths": 1,
                    "assists": 1,
                    "health": 0,
                    "damage": 345,
                    "shots_fired": 66,
                    "head_shots": 1,
                    "chest_shots": 45,
                    "other_shots": 20,
                    "kill_weapons": ['weapon_app_pistol'],
                    "defuse": False,
                    "plant": True,
                    "firstkill": True,
                }
            )
        ]

        controller.handle_update_players_stats(payload, self.match)
        player_stats.refresh_from_db()

        self.assertEqual(player_stats.kills, 4)
        self.assertEqual(player_stats.hs_kills, 2)
        self.assertEqual(player_stats.deaths, 2)
        self.assertEqual(player_stats.assists, 2)
        self.assertEqual(player_stats.damage, 690)
        self.assertEqual(player_stats.shots_fired, 132)
        self.assertEqual(player_stats.head_shots, 2)
        self.assertEqual(player_stats.chest_shots, 90)
        self.assertEqual(player_stats.other_shots, 40)
        self.assertEqual(player_stats.defuses, 0)
        self.assertEqual(player_stats.plants, 2)
        self.assertEqual(player_stats.firstkills, 1)

    def test_update_match_not_running(self):
        with self.assertRaises(Http404):
            controller.update_match(
                self.match.id,
                schemas.MatchUpdateSchema.from_orm(
                    {
                        'team_a_score': 0,
                        'team_b_score': 1,
                        'end_reason': 0,
                        'is_overtime': False,
                        'players_stats': [],
                    }
                ),
            )

        with self.assertRaises(Http404):
            controller.update_match(
                2904354758457854738543,
                schemas.MatchUpdateSchema.from_orm(
                    {
                        'team_a_score': 0,
                        'team_b_score': 1,
                        'end_reason': 0,
                        'is_overtime': False,
                        'players_stats': [],
                    }
                ),
            )

    def test_get_match(self):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()
        match = controller.get_match(self.user_1, self.match.id)
        self.assertEqual(match, self.match)

        with self.assertRaises(Http404):
            controller.get_match(self.user_3, self.match.id)

        self.match.status = models.Match.Status.FINISHED
        self.match.save()
        match = controller.get_match(self.user_3, self.match.id)
        self.assertEqual(match, self.match)

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.ws_friend_update_or_create')
    @mock.patch('matches.api.controller.websocket.ws_match_update')
    @mock.patch('matches.api.controller.handle_update_players_stats')
    def test_update_match(
        self,
        mock_handle_update_stats,
        mock_match_update,
        mock_friend_update,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'team_a_score': 0,
                    'team_b_score': 1,
                    'end_reason': 0,
                    'is_overtime': False,
                    'players_stats': [],
                }
            ),
        )
        mock_handle_update_stats.assert_called_once()
        mock_match_update.assert_called_once()
        self.assertEqual(self.match.team_a.score, 0)
        self.assertEqual(self.match.team_b.score, 1)

        mock_friend_update.asser_not_called()
        mock_update_user.asser_not_called()

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.ws_friend_update_or_create')
    @mock.patch('matches.api.controller.websocket.ws_match_update')
    @mock.patch('matches.api.controller.handle_update_players_stats')
    def test_update_match_finish(
        self,
        mock_handle_update_stats,
        mock_match_update,
        mock_friend_update,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'team_a_score': 10,
                    'team_b_score': 5,
                    'end_reason': 0,
                    'is_overtime': False,
                    'players_stats': [],
                }
            ),
        )
        mock_handle_update_stats.assert_called_once()
        mock_match_update.assert_called_once()
        self.assertEqual(self.match.team_a.score, 10)
        self.assertEqual(self.match.team_b.score, 5)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.FINISHED)

        mock_calls = [mock.call(self.user_1), mock.call(self.user_2)]
        mock_friend_update.assert_has_calls(mock_calls)
        mock_update_user.assert_has_calls(mock_calls)

    @mock.patch('matches.api.controller.websocket.ws_match_update')
    @mock.patch('matches.api.controller.handle_update_players_stats')
    def test_update_match_ot(self, mock_handle_update_stats, mock_match_update):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'team_a_score': 10,
                    'team_b_score': 11,
                    'end_reason': 0,
                    'is_overtime': True,
                    'players_stats': [],
                }
            ),
        )
        mock_handle_update_stats.assert_called_once()
        mock_match_update.assert_called_once()
        self.assertEqual(self.match.team_a.score, 10)
        self.assertEqual(self.match.team_b.score, 11)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.RUNNING)

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.ws_friend_update_or_create')
    @mock.patch('matches.api.controller.websocket.ws_match_update')
    @mock.patch('matches.api.controller.handle_update_players_stats')
    def test_update_match_ot_finish(
        self,
        mock_handle_update_stats,
        mock_match_update,
        mock_friend_update,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'team_a_score': 9,
                    'team_b_score': 11,
                    'end_reason': 0,
                    'is_overtime': True,
                    'players_stats': [],
                }
            ),
        )
        mock_handle_update_stats.assert_called_once()
        mock_match_update.assert_called_once()
        self.assertEqual(self.match.team_a.score, 9)
        self.assertEqual(self.match.team_b.score, 11)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.FINISHED)

        mock_calls = [mock.call(self.user_1), mock.call(self.user_2)]
        mock_friend_update.assert_has_calls(mock_calls)
        mock_update_user.assert_has_calls(mock_calls)
