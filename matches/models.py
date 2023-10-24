from __future__ import annotations

import os
from typing import List

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext as _

from appsettings.services import (
    matches_limit_per_server,
    matches_limit_per_server_gap,
    player_max_losing_level_points,
)

User = get_user_model()


def map_media_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    new_filename = f'{instance.sys_name}{extension}'
    return f'maps/thumbnails/{new_filename}'


class Server(models.Model):
    ip = models.GenericIPAddressField()
    name = models.CharField(max_length=32)
    port = models.IntegerField(default=30120)
    api_port = models.IntegerField(default=3000)

    @property
    def is_full(self) -> bool:
        """
        This property should be checked on every Match before creation.
        If it returns True, we should not create Match, but send an alert
        to admins and client application instead.
        """
        limit = matches_limit_per_server()
        return len(self.match_set.filter(status=Match.Status.RUNNING)) == limit

    @property
    def is_almost_full(self) -> bool:
        """
        This property should be checked on every Match before creation,
        so we can send alerts (email, etc) to admins if it returns True,
        which means that we need to create another FiveM server and key.
        """
        limit = matches_limit_per_server()
        gap = matches_limit_per_server_gap()
        return len(self.match_set.filter(status=Match.Status.RUNNING)) == (limit - gap)

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


class Map(models.Model):
    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=32)
    sys_name = models.CharField(max_length=32, unique=True)
    is_active = models.BooleanField(default=True)
    thumbnail = models.ImageField(upload_to=map_media_path, null=True)

    def __str__(self):
        return self.name


class Match(models.Model):
    class Meta:
        verbose_name_plural = 'matches'
        ordering = ['-end_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['end_date']),
            models.Index(fields=['start_date']),
        ]

    class Status(models.TextChoices):
        LOADING = 'loading'
        WARMUP = 'warmup'
        RUNNING = 'running'
        FINISHED = 'finished'
        CANCELLED = 'cancelled'

    class GameType(models.TextChoices):
        CUSTOM = 'custom'
        COMPETITIVE = 'competitive'

    class GameMode(models.IntegerChoices):
        SOLO = 1
        DEFUSE = 5
        DM = 20

    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    map = models.ForeignKey(Map, on_delete=models.CASCADE, default=1)
    create_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default='loading',
    )
    game_type = models.CharField(max_length=16, choices=GameType.choices)
    game_mode = models.IntegerField(choices=GameMode.choices)
    chat = models.JSONField(null=True)

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

    def finish(self):
        if self.status not in [Match.Status.RUNNING, Match.Status.WARMUP]:
            raise ValidationError(_('Unable to finish match while not running.'))

        self.status = Match.Status.FINISHED
        self.end_date = timezone.now()
        self.save()

        for player in self.players:
            player.user.account.apply_points_earned(player.points_earned)

    def warmup(self):
        if self.status != Match.Status.LOADING:
            raise ValidationError(_('Unable to warmup while not loaded.'))

        self.status = Match.Status.WARMUP
        self.save()

    def start(self):
        if self.status != Match.Status.WARMUP:
            raise ValidationError(_('Unable to start match while not warmed up.'))

        self.status = Match.Status.RUNNING
        self.start_date = timezone.now()
        self.save()

    def cancel(self):
        error_statuses = [Match.Status.FINISHED, Match.Status.CANCELLED]
        if self.status in error_statuses:
            raise ValidationError(_('Unable to cancel match after is finished.'))

        self.status = Match.Status.CANCELLED
        self.end_date = timezone.now()
        self.save()

    def get_user_team(self, user_id: int) -> MatchTeam:
        if user_id in [player.user_id for player in self.team_a.players]:
            return self.team_a
        elif user_id in [player.user_id for player in self.team_b.players]:
            return self.team_b
        else:
            return None


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

    def has_player(self, user):
        """
        Check if a user is in this team.
        """
        return self.players.filter(user=user).exists()

    def __str__(self):
        return f'#{self.id} - {self.name}'


class MatchPlayer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(MatchTeam, on_delete=models.CASCADE)
    level = models.IntegerField(editable=False)
    level_points = models.IntegerField(editable=False)

    @property
    def points_base(self):
        """
        Base calculation on top of player stats to determine how many points
        that player will earn after match.
        """
        assists = (self.stats.assists / 10) if self.stats.assists > 0 else 0
        plants = self.stats.plants * 2
        defuses = self.stats.defuses * 1.2
        kd = self.stats.kills - self.stats.deaths
        return int(round(assists + plants + defuses + kd))

    @property
    def points_cap(self):
        """
        Cap points so winners earn min of 10 and max of 30 points
        and losers min of -10 and max of -20.
        """
        if self.team.match.winner == self.team:
            if self.points_base + 10 < 10:
                return 10
            elif self.points_base + 10 > 30:
                return 30
            else:
                return self.points_base + 10
        else:
            if self.points_base - 25 > -10:
                return -10
            elif self.points_base - 25 < -20:
                return -20
            else:
                return self.points_base - 25

    @property
    def points_penalties(self):
        """
        The penalty is applied after all calculations, and the maximum that it can
        reach is the value at `appsettings.services.player_max_losing_level_points`.
        """
        afk_penalty = self.stats.afk**2
        if self.points_cap - afk_penalty > player_max_losing_level_points():
            return self.points_cap - afk_penalty

        return player_max_losing_level_points()

    @property
    def points_earned(self) -> int:
        """
        How many level points this player won in a match.
        """
        if self.team.match.status != Match.Status.FINISHED:
            return None

        points = self.points_cap
        if self.stats.afk:
            points = self.points_penalties

        if self.level <= 0 and self.level_points <= 0 and points < 0:
            return 0

        if self.level <= 0 and self.level_points - abs(points) < 0 and points < 0:
            return self.level_points * -1

        return points

    def save(self, *args, **kwargs):
        adding = True if self._state.adding else False

        if adding:
            self.level = self.user.account.level
            self.level_points = self.user.account.level_points
            super().save(*args, **kwargs)
            MatchPlayerStats.objects.create(player=self)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.steam_user.username}'


class MatchPlayerStats(models.Model):
    PERCENTAGE_STATS = [
        'accuracy',
        'head_accuracy',
        'chest_accuracy',
        'others_accuracy',
        'hsk',
    ]

    RATIO_STATS = [
        'kdr',
        'kda',
        'ahk',
        'ahr',
    ]

    ROUND_STATS = [('adr', 'damage')]

    player = models.OneToOneField(
        MatchPlayer,
        on_delete=models.CASCADE,
        related_name='stats',
    )
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
        return self.player.team.match.rounds - self.afk

    @property
    def clutches(self) -> int:
        """
        Rounds wins on vs[N] situations.
        """
        return sum(
            [
                self.clutch_v1,
                self.clutch_v2,
                self.clutch_v3,
                self.clutch_v4,
                self.clutch_v5,
            ]
        )

    @property
    def shots_hit(self) -> int:
        """
        All shots fired that hit a target.
        """
        return sum([self.head_shots, self.chest_shots, self.other_shots])

    @property
    def frag(self) -> str:
        """
        A string containing resumed stats : kills / deaths / assists.
        """
        return f'{self.kills}/{self.deaths}/{self.assists}'

    @property
    def adr(self) -> float:
        """
        Average damage per round.
        """
        if self.rounds_played > 0:
            return round(float(self.damage / self.rounds_played), 2)
        return round(float(0), 2)

    @property
    def kdr(self) -> float:
        """
        Kill/death ratio.
        """
        if self.deaths > 0:
            return round(float(self.kills / self.deaths), 2)
        return round(float(self.kills), 2)

    @property
    def kda(self) -> float:
        """
        Kills, deaths and assists ratio.
        """
        if self.deaths > 0:
            return round(float((self.kills + self.assists) / self.deaths), 2)
        return round(float(self.kills + self.assists), 2)

    @property
    def ahk(self) -> float:
        """
        Average headshot kills per shot.
        """
        if self.shots_fired > 0:
            return round(float(self.hs_kills / self.shots_fired), 2)
        return round(float(0), 2)

    @property
    def ahr(self) -> float:
        """
        Average headshots per round.
        """
        if self.player.team.match.rounds > 0:
            return round(float(self.head_shots / self.player.team.match.rounds), 2)
        return round(float(0), 2)

    @property
    def hsk(self) -> int:
        """
        Percentage of hs kills by kills.
        """
        if self.kills > 0:
            return int(round((self.hs_kills / self.kills) * 100))
        return 0

    @property
    def accuracy(self) -> int:
        """
        Percentage of shots that hit a target.
        """
        if self.shots_fired > 0:
            return int((self.shots_hit / self.shots_fired) * 100)
        return 0

    @property
    def head_accuracy(self) -> int:
        """
        Percentage of shots that hits a head.
        """
        if self.shots_hit > 0:
            return int((self.head_shots / self.shots_hit) * 100)
        return 0

    @property
    def chest_accuracy(self) -> int:
        """
        Percentage of shots that hits a chest/torax.
        """
        if self.shots_hit > 0:
            return int(round((self.chest_shots / self.shots_hit) * 100))
        return 0

    @property
    def others_accuracy(self) -> int:
        """
        Percentage of shots that hits other body parts.
        """
        if self.shots_hit > 0:
            return int(round((self.other_shots / self.shots_hit) * 100))
        return 0

    def __str__(self):
        return f'{self.player.user.steam_user.username}'


class BetaUser(models.Model):
    steamid_hex = models.CharField(max_length=64, unique=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=32)
    date_add = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'beta users'
        ordering = ['-date_add']
        indexes = [models.Index(fields=['email'])]

    def save(self, *args, **kwargs):
        if settings.ENVIRONMENT != settings.LOCAL:
            payload = {'steamid': self.steamid_hex, 'username': self.username}
            server = Server.objects.first()
            requests.post(
                f'http://{server.ip}:{server.port}/core/addAllowlist',
                json=payload,
            )

        super(BetaUser, self).save(*args, **kwargs)

    def __str__(self):
        return self.username


@receiver(post_save, sender=MatchPlayer)
def match_team_save_signal(sender, instance, created, **kwargs):
    if created:
        instance.user.status = User.Statuses.IN_GAME
        instance.user.save()


@receiver(post_save, sender=Match)
def match_update_signal(sender, instance, created, **kwargs):
    if instance.status in [Match.Status.CANCELLED, Match.Status.FINISHED]:
        players_ids = [player.user.id for player in instance.players]
        User.objects.filter(id__in=players_ids).update(status=User.Statuses.ONLINE)
