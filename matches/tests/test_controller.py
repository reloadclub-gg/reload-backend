from unittest import mock

from django.conf import settings
from django.utils import timezone
from model_bakery import baker
from ninja.errors import Http404

from accounts.utils import steamid64_to_hex
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
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        self.match_t1 = self.match.matchteam_set.create(name=self.team1.name, score=10)
        self.match_t2 = self.match.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=self.match_t1, user=self.user_1)
        baker.make(models.MatchPlayer, team=self.match_t2, user=self.user_2)

    def test_get_user_matches(self):
        match2 = baker.make(
            models.Match,
            server=self.server,
            status=models.Match.Status.FINISHED,
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        team1 = match2.matchteam_set.create(name=self.team1.name, score=10)
        match2.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=team1, user=self.user_1)

        results = controller.get_user_matches(self.user_1)
        self.assertEqual(len(results), 2)

        match = baker.make(
            models.Match,
            server=self.server,
            status=models.Match.Status.FINISHED,
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10)
        match.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=team1, user=self.user_2)

        results = controller.get_user_matches(self.user_1, self.user_2.id)
        self.assertEqual(len(results), 2)

    def test_handle_update_players_stats(self):
        self.user_1.account.steamid = '04085177656553014'
        self.user_1.account.save()
        self.user_1.account.refresh_from_db()
        payload = [
            schemas.MatchUpdatePlayerStats.from_orm(
                {
                    "steamid": steamid64_to_hex(self.user_1.account.steamid),
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
        self.assertEqual(player_stats.double_kills, 1)

        payload = [
            schemas.MatchUpdatePlayerStats.from_orm(
                {
                    "steamid": steamid64_to_hex(self.user_1.account.steamid),
                    "kills": 4,
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

        self.assertEqual(player_stats.kills, 6)
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
        self.assertEqual(player_stats.double_kills, 1)
        self.assertEqual(player_stats.quadra_kills, 1)

    def test_update_match_not_found(self):
        self.match.status = models.Match.Status.CANCELLED
        self.match.save()
        with self.assertRaises(Http404):
            controller.update_match(
                self.match.id,
                schemas.MatchUpdateSchema.from_orm(
                    {
                        'teams': [
                            {'name': self.match_t1.name, 'score': 0, 'players': []},
                            {'name': self.match_t2.name, 'score': 1, 'players': []},
                        ],
                        'end_reason': 0,
                        'is_overtime': False,
                    }
                ),
            )

        self.match.status = models.Match.Status.FINISHED
        self.match.save()
        with self.assertRaises(Http404):
            controller.update_match(
                self.match.id,
                schemas.MatchUpdateSchema.from_orm(
                    {
                        'teams': [
                            {'name': self.match_t1.name, 'score': 0, 'players': []},
                            {'name': self.match_t2.name, 'score': 1, 'players': []},
                        ],
                        'end_reason': 0,
                        'is_overtime': False,
                    }
                ),
            )

        with self.assertRaises(Http404):
            controller.update_match(
                2904354758457854738543,
                schemas.MatchUpdateSchema.from_orm(
                    {
                        'teams': [
                            {'name': self.match_t1.name, 'score': 0, 'players': []},
                            {'name': self.match_t2.name, 'score': 1, 'players': []},
                        ],
                        'end_reason': 0,
                        'is_overtime': False,
                    }
                ),
            )

    def test_get_match(self):
        self.match.status = models.Match.Status.WARMUP
        self.match.save()
        match = controller.get_match(self.user_1, self.match.id)
        self.assertEqual(match, self.match)

        with self.assertRaises(Http404):
            controller.get_match(self.user_3, self.match.id)

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

        self.match.status = models.Match.Status.CANCELLED
        self.match.save()
        with self.assertRaises(Http404):
            controller.get_match(self.user_1, self.match.id)

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.websocket.ws_match_update')
    @mock.patch('matches.api.controller.handle_update_players_stats')
    def test_update_match(
        self,
        mock_handle_update_stats,
        mock_match_update,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'teams': [
                        {'name': self.match_t1.name, 'score': 0, 'players': []},
                        {'name': self.match_t2.name, 'score': 1, 'players': []},
                    ],
                    'end_reason': 0,
                    'is_overtime': False,
                }
            ),
        )
        mock_handle_update_stats.assert_called_once()
        mock_match_update.assert_called_once()
        self.assertEqual(self.match.team_a.score, 0)
        self.assertEqual(self.match.team_b.score, 1)

        mock_update_user.asser_not_called()

    @mock.patch('matches.api.controller.websocket.ws_match_update')
    def test_update_match_start(self, mock_match_update):
        self.match.status = models.Match.Status.WARMUP
        self.match.start_date = None
        self.match.save()

        self.assertIsNone(self.match.start_date)
        self.assertEqual(self.match.status, models.Match.Status.WARMUP)

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm({'status': 'running'}),
        )

        self.match.refresh_from_db()
        mock_match_update.assert_called_once()
        self.assertIsNotNone(self.match.start_date)
        self.assertEqual(self.match.status, models.Match.Status.RUNNING)

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.websocket.ws_match_update')
    @mock.patch('matches.api.controller.handle_update_players_stats')
    def test_update_match_finish(
        self,
        mock_handle_update_stats,
        mock_match_update,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        self.match_t1.score = 12
        self.match_t1.save()
        self.match_t2.score = 6
        self.match_t2.save()

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'teams': [
                        {'name': self.match_t1.name, 'score': 13, 'players': []},
                        {'name': self.match_t2.name, 'score': 6, 'players': []},
                    ],
                    'end_reason': 0,
                    'is_overtime': False,
                }
            ),
        )
        mock_handle_update_stats.assert_called_once()
        mock_match_update.assert_called_once()
        self.assertEqual(self.match.team_a.score, 13)
        self.assertEqual(self.match.team_b.score, 6)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.FINISHED)

        mock_calls = [mock.call(self.user_1), mock.call(self.user_2)]
        mock_update_user.assert_has_calls(mock_calls)

    @mock.patch('matches.api.controller.websocket.ws_match_update')
    @mock.patch('matches.api.controller.handle_update_players_stats')
    def test_update_match_ot(self, mock_handle_update_stats, mock_match_update):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        self.match_t1.score = 13
        self.match_t1.save()
        self.match_t2.score = 13
        self.match_t2.save()

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'teams': [
                        {
                            'name': self.match_t1.name,
                            'score': settings.MATCH_ROUNDS_TO_WIN + 1,
                            'players': [],
                        },
                        {
                            'name': self.match_t2.name,
                            'score': settings.MATCH_ROUNDS_TO_WIN,
                            'players': [],
                        },
                    ],
                    'end_reason': 0,
                    'is_overtime': True,
                }
            ),
        )
        mock_handle_update_stats.assert_called_once()
        mock_match_update.assert_called_once()
        self.assertEqual(self.match.team_a.score, settings.MATCH_ROUNDS_TO_WIN + 1)
        self.assertEqual(self.match.team_b.score, settings.MATCH_ROUNDS_TO_WIN)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.RUNNING)

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.websocket.ws_match_update')
    @mock.patch('matches.api.controller.handle_update_players_stats')
    def test_update_match_ot_finish(
        self,
        mock_handle_update_stats,
        mock_match_update,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        self.match_t1.score = 13
        self.match_t1.save()
        self.match_t2.score = 14
        self.match_t2.save()

        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'teams': [
                        {
                            'name': self.match_t1.name,
                            'score': settings.MATCH_ROUNDS_TO_WIN,
                            'players': [],
                        },
                        {
                            'name': self.match_t2.name,
                            'score': settings.MATCH_ROUNDS_TO_WIN + 2,
                            'players': [],
                        },
                    ],
                    'end_reason': 0,
                    'is_overtime': True,
                }
            ),
        )
        mock_handle_update_stats.assert_called_once()
        mock_match_update.assert_called_once()
        self.assertEqual(self.match.team_a.score, settings.MATCH_ROUNDS_TO_WIN)
        self.assertEqual(self.match.team_b.score, settings.MATCH_ROUNDS_TO_WIN + 2)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.FINISHED)

        mock_calls = [mock.call(self.user_1), mock.call(self.user_2)]
        mock_update_user.assert_has_calls(mock_calls)

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.websocket.ws_match_delete')
    def test_cancel_match_loading(
        self,
        mock_match_delete,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.LOADING
        self.match.save()

        controller.cancel_match(self.match.id)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.CANCELLED)

        mock_match_delete.assert_called_once()
        self.assertEqual(mock_update_user.call_count, 2)

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.websocket.ws_match_delete')
    def test_cancel_match_running(
        self,
        mock_match_delete,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        controller.cancel_match(self.match.id)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.CANCELLED)

        mock_match_delete.assert_called_once()
        self.assertEqual(mock_update_user.call_count, 2)

    @mock.patch('matches.api.controller.ws_update_user')
    @mock.patch('matches.api.controller.websocket.ws_match_delete')
    def test_cancel_match_warmup(
        self,
        mock_match_delete,
        mock_update_user,
    ):
        self.match.status = models.Match.Status.WARMUP
        self.match.save()

        controller.cancel_match(self.match.id)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, models.Match.Status.CANCELLED)

        mock_match_delete.assert_called_once()
        self.assertEqual(mock_update_user.call_count, 2)

    def test_cancel_match_error(self):
        self.match.status = models.Match.Status.CANCELLED
        self.match.save()

        with self.assertRaises(Http404):
            controller.cancel_match(self.match.id)

    def test_update_scores_inverted(self):
        self.match.status = models.Match.Status.RUNNING
        self.match.save()

        self.match_t1.score = 0
        self.match_t1.save()
        self.match_t2.score = 1
        self.match_t2.save()

        # inversion
        controller.update_scores(
            self.match,
            [
                schemas.MatchUpdateTeam.from_orm(
                    {
                        'name': self.match_t1.name,
                        'score': 2,
                        'players': [],
                    }
                ),
                schemas.MatchUpdateTeam.from_orm(
                    {
                        'name': self.match_t2.name,
                        'score': 1,
                        'players': [],
                    }
                ),
            ],
            1,  # end_reason -> ENEMY_DEAD
        )
        self.assertEqual(self.match.team_a.score, 0)
        self.assertEqual(self.match.team_b.score, 2)

        controller.update_scores(
            self.match,
            [
                schemas.MatchUpdateTeam.from_orm(
                    {
                        'name': self.match_t1.name,
                        'score': 0,
                        'players': [],
                    }
                ),
                schemas.MatchUpdateTeam.from_orm(
                    {
                        'name': self.match_t2.name,
                        'score': 3,
                        'players': [],
                    }
                ),
            ],
            1,  # end_reason -> ENEMY_DEAD
        )
        self.assertEqual(self.match.team_a.score, 0)
        self.assertEqual(self.match.team_b.score, 3)

        controller.update_scores(
            self.match,
            [
                schemas.MatchUpdateTeam.from_orm(
                    {
                        'name': self.match_t1.name,
                        'score': 1,
                        'players': [],
                    }
                ),
                schemas.MatchUpdateTeam.from_orm(
                    {
                        'name': self.match_t2.name,
                        'score': 3,
                        'players': [],
                    }
                ),
            ],
            1,  # end_reason -> ENEMY_DEAD
        )
        self.assertEqual(self.match.team_a.score, 1)
        self.assertEqual(self.match.team_b.score, 3)

        # inversion
        controller.update_scores(
            self.match,
            [
                schemas.MatchUpdateTeam.from_orm(
                    {
                        'name': self.match_t1.name,
                        'score': 4,
                        'players': [],
                    }
                ),
                schemas.MatchUpdateTeam.from_orm(
                    {
                        'name': self.match_t2.name,
                        'score': 1,
                        'players': [],
                    }
                ),
            ],
            1,  # end_reason -> ENEMY_DEAD
        )
        self.assertEqual(self.match.team_a.score, 1)
        self.assertEqual(self.match.team_b.score, 4)

        self.match_t1.score = 8
        self.match_t1.save()
        self.match_t2.score = 12
        self.match_t2.save()

        # inversion
        controller.update_match(
            self.match.id,
            schemas.MatchUpdateSchema.from_orm(
                {
                    'teams': [
                        {'name': self.match_t1.name, 'score': 13, 'players': []},
                        {'name': self.match_t2.name, 'score': 8, 'players': []},
                    ],
                    'end_reason': 0,
                    'is_overtime': False,
                }
            ),
        )
        self.match.refresh_from_db()
        self.assertEqual(self.match.team_a.score, 8)
        self.assertEqual(self.match.team_b.score, 13)
        self.assertEqual(self.match.status, models.Match.Status.FINISHED)
