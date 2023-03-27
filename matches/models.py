from __future__ import annotations

from typing import List

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q

from appsettings.services import matches_limit_per_server, matches_limit_per_server_gap

User = get_user_model()


class Server(models.Model):

    ip = models.GenericIPAddressField()
    name = models.CharField(max_length=32)
    key = models.TextField()

    @property
    def is_full(self) -> bool:
        """
        This property should be checked on every Match before creation.
        If it returns True, we should not create Match, but send an alert
        to admins and client application instead.
        """
        limit = matches_limit_per_server()
        return len(self.match_set.all()) == limit

    @property
    def is_almost_full(self) -> bool:
        """
        This property should be checked on every Match before creation,
        so we can send alerts (email, etc) to admins if it returns True,
        which means that we need to create another FiveM server and key.
        """
        limit = matches_limit_per_server()
        gap = matches_limit_per_server_gap()
        return len(self.match_set.all()) == (limit - gap)

    @staticmethod
    def get_idle() -> Server:
        """
        Fetch and return a server that isn't full and is able to
        host a new match.
        """
        servers = Server.objects.all()
        for server in servers:
            if not server.is_full:
                return server

        return None

    def __str__(self):
        return f'{self.name} - {self.ip}'


class Match(models.Model):
    class Status(models.IntegerChoices):
        LOADING = 0
        RUNNING = 1
        FINISHED = 2

    class GameType(models.TextChoices):
        CUSTOM = 'custom'
        COMPETITIVE = 'competitive'

    class GameMode(models.IntegerChoices):
        SOLO = 1
        DEFUSE = 5
        DM = 20

    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(
        choices=Status.choices, default=0, blank=True, null=True
    )
    game_type = models.CharField(max_length=16, choices=GameType.choices)
    game_mode = models.IntegerField(choices=GameMode.choices)

    @property
    def team_a(self) -> MatchTeam:
        """
        Return a team (first result on `self.teams`) from this match.
        """
        return self.teams[0]

    @property
    def team_b(self) -> MatchTeam:
        """
        Return a team (second/last result on `self.teams`) from this match.
        """
        return self.teams[1]

    @property
    def teams(self) -> List[MatchTeam]:
        """
        Return all (should always be 2 max) teams from this match.
        """
        team_a = None
        team_b = None
        for team in self.matchteam_set.all():
            if not team_a:
                team_a = team
            else:
                team_b = team

        return [team_a, team_b]

    @property
    def rounds(self) -> int:
        """
        How many rounds were played on this match.
        Usefull for calculations on players stats.
        """
        return self.team_a.score + self.team_b.score

    @property
    def winner(self) -> MatchTeam:
        """
        Which team is winning or won.
        Returns `None` in case of draw or non started match.
        """
        if self.team_a.score == self.team_b.score:
            return None
        elif self.team_a.score > self.team_b.score:
            return self.team_a

        return self.team_b

    @property
    def players(self) -> List[MatchPlayer]:
        """
        Fetch and return all players that are in match.
        """
        return MatchPlayer.objects.filter(Q(team=self.team_a) | Q(team=self.team_b))

    def __str__(self):
        if self.team_a and self.team_b:
            return f'#{self.id} - {self.team_a.name} vs {self.team_b.name}'
        return f'#{self.id} - waiting for team creation'


class MatchTeam(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    score = models.IntegerField(default=0, blank=True, null=True)

    @property
    def players(self) -> List[MatchPlayer]:
        """
        Fetch and return all players that are in team.
        """
        return MatchPlayer.objects.filter(team=self)

    def __str__(self):
        return f'#{self.id} - {self.name}'


class MatchPlayer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(MatchTeam, on_delete=models.CASCADE)
    kills = models.IntegerField(blank=True, null=True, default=0)
    deaths = models.IntegerField(blank=True, null=True, default=0)
    assists = models.IntegerField(blank=True, null=True, default=0)
    damage = models.IntegerField(blank=True, null=True, default=0)
    hs_kills = models.IntegerField(blank=True, null=True, default=0)
    afk = models.IntegerField(blank=True, null=True, default=0)
    plants = models.IntegerField(blank=True, null=True, default=0)
    defuses = models.IntegerField(blank=True, null=True, default=0)
    double_kills = models.IntegerField(blank=True, null=True, default=0)
    triple_kills = models.IntegerField(blank=True, null=True, default=0)
    quadra_kills = models.IntegerField(blank=True, null=True, default=0)
    aces = models.IntegerField(blank=True, null=True, default=0)
    clutch_v1 = models.IntegerField(blank=True, null=True, default=0)
    clutch_v2 = models.IntegerField(blank=True, null=True, default=0)
    clutch_v3 = models.IntegerField(blank=True, null=True, default=0)
    clutch_v4 = models.IntegerField(blank=True, null=True, default=0)
    clutch_v5 = models.IntegerField(blank=True, null=True, default=0)
    firstkills = models.IntegerField(blank=True, null=True, default=0)
    shots_fired = models.IntegerField(blank=True, null=True, default=0)
    head_shots = models.IntegerField(blank=True, null=True, default=0)
    chest_shots = models.IntegerField(blank=True, null=True, default=0)
    other_shots = models.IntegerField(blank=True, null=True, default=0)

    @property
    def rounds_played(self) -> int:
        """
        All rounds that a player has played.
        """
        return self.team.match.rounds - self.afk

    @property
    def clutches(self) -> int:
        """
        Rounds wins on vs[N] situations.
        """
        return sum(
            self.clutch_v1,
            self.clutch_v2,
            self.clutch_v3,
            self.clutch_v4,
            self.clutch_v5,
        )

    @property
    def shots_hit(self) -> int:
        """
        All shots fired that hit a target.
        """
        return sum(self.head_shots, self.chest_shots, self.lef_shots)

    @property
    def frag(self) -> str:
        """
        A string containing resumed stats : kills / deaths / assists.
        """
        return f'{self.kills} / {self.deaths} / {self.assists}'

    @property
    def adr(self) -> float:
        """
        Average damage per round.
        """
        if self.rounds_played > 0:
            return float('{:0.2f}'.format(self.damage / self.rounds_played))
        return float(0)

    @property
    def kdr(self) -> float:
        """
        Kill/death ratio.
        """
        if self.deaths > 0:
            return float('{:0.2f}'.format(self.kills / self.deaths))
        return float('{:0.2f}'.format(self.kills))

    @property
    def kda(self) -> float:
        """
        Kills, deaths and assists ratio.
        """
        if self.deaths > 0:
            return float('{:0.2f}'.format((self.kills + self.assists) / self.deaths))
        return float('{:0.2f}'.format(self.kills + self.assists))

    @property
    def ahk(self) -> float:
        """
        Average headshot kills per shot.
        """
        if self.shots_fired > 0:
            return float('{:0.2f}'.format(self.hs_kills / self.shots_fired))
        return float(0)

    @property
    def ahr(self) -> float:
        """
        Average headshots per round.
        """
        if self.shots_fired > 0:
            return float('{:0.2f}'.format(self.head_shots / self.team.match.rounds))
        return float(0)

    @property
    def accuracy(self) -> float:
        """
        Average accuracy per shot.
        """
        if self.shots_fired > 0:
            return float('{:0.2f}'.format(self.hit_shots / self.shots_fired))
        return float(0)

    @property
    def head_accuracy(self) -> float:
        """
        Average accuracy per shot that hit a head.
        """
        if self.hit_shots > 0:
            return float('{:0.2f}'.format(self.head_shots / self.hit_shots))
        return float(0)

    @property
    def chest_accuracy(self) -> float:
        """
        Average accuracy per shot that hit a chest/torax.
        """
        if self.hit_shots > 0:
            return float('{:0.2f}'.format(self.chest_shots / self.hit_shots))
        return float(0)

    @property
    def others_accuracy(self) -> float:
        """
        Average accuracy per shot that hit other body parts.
        """
        if self.hit_shots > 0:
            return float('{:0.2f}'.format(self.other_shots / self.hit_shots))
        return float(0)

    @property
    def points_earned(self) -> int:
        """
        How many level points this player won in a match.
        """
        if self.team.match.status != Match.Status.FINISHED:
            return None

        if self.rounds_played > 0:
            step1 = (self.assists / 10) if self.assists > 0 else 0
            step2 = self.plants * 2
            step3 = self.defuses * 1.2
            step4 = self.kills - self.deaths
            result1 = step1 + step2 + step3 + step4
            result1 = int(round(result1))

            if self.team.match.winner == self.team:
                result2 = int(round(result1 + 10))
                # if result2 is lesser then 20 or greater then 30 on victory,
                # adjust it to 20 or 30
                if result2 < 10:
                    result2 = 10
                elif result2 > 30:
                    result2 = 30
            else:
                result2 = int(round(result1 - 25))
                # if result2 is lesser then -20 or greater then -10 on defeat,
                # adjust it to -20 or -10
                if result2 < -20:
                    result2 = -20
                elif result2 > -10:
                    result2 = -10

            # Apply afk penalties
            level_points = result2 - self.afk * 3
            return level_points

        return 0

    def __str__(self):
        return f'{self.user.steam_user.username}'
