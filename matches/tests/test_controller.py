from django.utils import timezone
from model_bakery import baker

from core.tests import TestCase
from matches.api import controller
from matches.models import Match, MatchPlayer, Server
from matchmaking.tests.mixins import TeamsMixin


class MatchesControllerTestCase(TeamsMixin, TestCase):
    def test_get_user_matches(self):
        server = baker.make(Server)
        match1 = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match1.matchteam_set.create(name=self.team1.name, score=10)
        match1.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(MatchPlayer, team=team1, user=self.user_1)

        match2 = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match2.matchteam_set.create(name=self.team1.name, score=10)
        match2.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(MatchPlayer, team=team1, user=self.user_1)

        results = controller.get_user_matches(self.user_1)
        self.assertEqual(len(results), 2)
        self.assertTrue(match1 in results)
        self.assertTrue(match2 in results)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10)
        match.matchteam_set.create(name=self.team2.name, score=6)
        baker.make(MatchPlayer, team=team1, user=self.user_2)

        results = controller.get_user_matches(self.user_1, self.user_2.id)
        self.assertEqual(len(results), 1)
        self.assertTrue(match in results)
