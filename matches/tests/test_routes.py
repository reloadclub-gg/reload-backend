from django.test import override_settings
from django.utils import timezone
from model_bakery import baker

from core.tests import APIClient, TestCase
from matches import models
from matches.api import schemas
from pre_matches.tests.mixins import TeamsMixin


class MatchesRoutesTestCase(TeamsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient('/api/matches')

    def test_match_detail(self):
        server = baker.make(models.Server)
        match = baker.make(models.Match, server=server)
        team1 = match.matchteam_set.create(name=self.team1.name)
        match.matchteam_set.create(name=self.team2.name)
        baker.make(models.MatchPlayer, user=self.user_1, team=team1)
        r = self.api.call('get', f'/{match.id}', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), schemas.MatchSchema.from_orm(match).dict())

    def test_match_list(self):
        server = baker.make(models.Server)
        match1 = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match1.matchteam_set.create(name=self.team1.name, score=10)
        match1.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=team1, user=self.user_1)

        match2 = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match2.matchteam_set.create(name=self.team1.name, score=10)
        match2.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=team1, user=self.user_1)
        r = self.api.call('get', '/', token=self.user_1.auth.token)
        self.assertEqual(r.json().get('count'), 2)

        match = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10)
        match.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=team1, user=self.user_2)
        r = self.api.call(
            'get',
            f'/?user_id={self.user_2.id}',
            token=self.user_1.auth.token,
        )
        self.assertEqual(r.json().get('count'), 1)

    @override_settings(DEBUG=False)
    def test_update(self):
        server = baker.make(models.Server)
        match = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.RUNNING,
            end_date=timezone.now(),
        )
        match.matchteam_set.create(name=self.team1.name, score=10)
        match.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(models.MatchPlayer, team=match.team_a, user=self.user_1)
        baker.make(models.MatchPlayer, team=match.team_b, user=self.user_2)

        r = self.api.call(
            'patch',
            f'/{match.id}',
            data={
                'team_a_score': 9,
                'team_b_score': 11,
                'end_reason': 0,
                'is_overtime': True,
                'players_stats': [],
            },
            token=self.user_1.auth.token,
        )

        self.assertEqual(match.team_a.score, 9)
        self.assertEqual(match.team_b.score, 11)
