from datetime import timedelta

from django.utils import timezone
from model_bakery import baker

from core.tests import TestCase
from pre_matches.tests.mixins import TeamsMixin

from .. import models, tasks


class MatchesTasksTestCase(TeamsMixin, TestCase):
    def test_delete_old_cancelled_matches(self):
        server = baker.make(models.Server)
        match = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.CANCELLED,
            end_date=timezone.now() - timedelta(hours=12),
        )
        match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(models.MatchPlayer, team=match.team_a, user=self.user_1)
        baker.make(models.MatchPlayer, team=match.team_b, user=self.user_2)

        tasks.delete_old_cancelled_matches()
        self.assertEqual(models.Match.objects.all().count(), 1)

        match.end_date = timezone.now() - timedelta(days=1)
        match.save()

        tasks.delete_old_cancelled_matches()
        self.assertEqual(models.Match.objects.all().count(), 0)
