from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from model_bakery import baker

from pre_matches.tests.mixins import TeamsMixin

from .. import models

User = get_user_model()


class FinishedMatchesMixin(TeamsMixin):
    def setUp(self):
        super().setUp()

        server = baker.make(models.Server)
        self.match1 = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = self.match1.matchteam_set.create(
            name=self.team1.name,
            score=settings.MATCH_ROUNDS_TO_WIN,
        )
        team2 = self.match1.matchteam_set.create(name=self.team2.name, score=5)
        baker.make(models.MatchPlayer, team=team1, user=self.user_1)
        baker.make(models.MatchPlayer, team=team1, user=self.user_2)
        baker.make(models.MatchPlayer, team=team1, user=self.user_3)
        baker.make(models.MatchPlayer, team=team1, user=self.user_4)
        baker.make(models.MatchPlayer, team=team1, user=self.user_5)
        baker.make(models.MatchPlayer, team=team2, user=self.user_6)
        baker.make(models.MatchPlayer, team=team2, user=self.user_7)
        baker.make(models.MatchPlayer, team=team2, user=self.user_8)
        baker.make(models.MatchPlayer, team=team2, user=self.user_9)
        baker.make(models.MatchPlayer, team=team2, user=self.user_10)

        self.match2 = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = self.match2.matchteam_set.create(
            name=self.team1.name,
            score=settings.MATCH_ROUNDS_TO_WIN,
        )
        team2 = self.match2.matchteam_set.create(name=self.team2.name, score=5)
        baker.make(models.MatchPlayer, team=team1, user=self.user_1)
        baker.make(models.MatchPlayer, team=team1, user=self.user_2)
        baker.make(models.MatchPlayer, team=team1, user=self.user_3)
        baker.make(models.MatchPlayer, team=team1, user=self.user_4)
        baker.make(models.MatchPlayer, team=team1, user=self.user_5)
        baker.make(models.MatchPlayer, team=team2, user=self.user_6)
        baker.make(models.MatchPlayer, team=team2, user=self.user_7)
        baker.make(models.MatchPlayer, team=team2, user=self.user_8)
        baker.make(models.MatchPlayer, team=team2, user=self.user_9)
        baker.make(models.MatchPlayer, team=team2, user=self.user_10)

        self.match3 = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = self.match3.matchteam_set.create(name=self.team1.name, score=5)
        team2 = self.match3.matchteam_set.create(
            name=self.team2.name,
            score=settings.MATCH_ROUNDS_TO_WIN,
        )
        baker.make(models.MatchPlayer, team=team1, user=self.user_1)
        baker.make(models.MatchPlayer, team=team1, user=self.user_2)
        baker.make(models.MatchPlayer, team=team1, user=self.user_3)
        baker.make(models.MatchPlayer, team=team1, user=self.user_4)
        baker.make(models.MatchPlayer, team=team1, user=self.user_5)
        baker.make(models.MatchPlayer, team=team2, user=self.user_6)
        baker.make(models.MatchPlayer, team=team2, user=self.user_7)
        baker.make(models.MatchPlayer, team=team2, user=self.user_8)
        baker.make(models.MatchPlayer, team=team2, user=self.user_9)
        baker.make(models.MatchPlayer, team=team2, user=self.user_10)


class RunningMatchesMixin(TeamsMixin):
    def setUp(self):
        super().setUp()

        server = baker.make(models.Server)
        self.match1 = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.RUNNING,
        )
        team1 = self.match1.matchteam_set.create(name=self.team1.name)
        team2 = self.match1.matchteam_set.create(name=self.team2.name)
        baker.make(models.MatchPlayer, team=team1, user=self.user_1)
        baker.make(models.MatchPlayer, team=team1, user=self.user_2)
        baker.make(models.MatchPlayer, team=team1, user=self.user_3)
        baker.make(models.MatchPlayer, team=team1, user=self.user_4)
        baker.make(models.MatchPlayer, team=team1, user=self.user_5)
        baker.make(models.MatchPlayer, team=team2, user=self.user_6)
        baker.make(models.MatchPlayer, team=team2, user=self.user_7)
        baker.make(models.MatchPlayer, team=team2, user=self.user_8)
        baker.make(models.MatchPlayer, team=team2, user=self.user_9)
        baker.make(models.MatchPlayer, team=team2, user=self.user_10)

        self.match2 = baker.make(
            models.Match,
            server=server,
            status=models.Match.Status.RUNNING,
        )
        team3 = self.match2.matchteam_set.create(name=self.team3.name)
        team4 = self.match2.matchteam_set.create(name=self.team4.name)
        baker.make(models.MatchPlayer, team=team3, user=self.user_11)
        baker.make(models.MatchPlayer, team=team3, user=self.user_12)
        baker.make(models.MatchPlayer, team=team3, user=self.user_13)
        baker.make(models.MatchPlayer, team=team3, user=self.user_14)
        baker.make(models.MatchPlayer, team=team3, user=self.user_15)
        baker.make(models.MatchPlayer, team=team4, user=self.user_16)
        baker.make(models.MatchPlayer, team=team4, user=self.user_17)
        baker.make(models.MatchPlayer, team=team4, user=self.user_18)
        baker.make(models.MatchPlayer, team=team4, user=self.user_19)
        baker.make(models.MatchPlayer, team=team4, user=self.user_20)
