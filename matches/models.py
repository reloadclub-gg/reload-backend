from django.contrib.auth import get_user_model
from django.db import models

from core.utils import generate_random_string

User = get_user_model()


class Match(models.Model):
    class Teams(models.TextChoices):
        TEAM_A = 'team_a'
        TEAM_B = 'team_b'

    class Status(models.IntegerChoices):
        LOADING = 0
        RUNNING = 1
        FINISHED = 2

    class GameType(models.IntegerChoices):
        CUSTOM = 0
        COMPETITIVE = 1

    class GameMode(models.IntegerChoices):
        SOLO = 1
        DEFUSE = 5
        DM = 20

    create_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    winner_team = models.CharField(
        max_length=16, choices=Teams.choices, blank=True, null=True
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=0, blank=True, null=True
    )
    team_a_score = models.IntegerField(default=0, blank=True, null=True)
    team_b_score = models.IntegerField(default=0, blank=True, null=True)
    password = models.CharField(max_length=16, blank=True, null=True)
    game_type = models.CharField(
        max_length=16, choices=GameType.choices, blank=True, null=True
    )
    game_mode = models.IntegerField(choices=GameMode.choices, blank=True, null=True)

    def generate_match_password(self) -> str:
        """
        Randomize a unique match password and assure that
        all matches will have different passwords.
        """
        password = generate_random_string(length=10)
        already = False
        for match in Match.objects.all():
            if match.password == password:
                already = True

        if already:
            self.generate_match_password()

        return password

    def save(self, *args, **kwargs):
        if not self.pk:
            self.password = self.generate_match_password()
        super().save(*args, **kwargs)

    @property
    def rounds(self) -> int:
        return self.team_a_score + self.team_b_score


class MatchPlayer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches_set')
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    team = models.CharField(max_length=16, choices=Match.Teams.choices)
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
    leg_shots = models.IntegerField(blank=True, null=True, default=0)

    @property
    def rounds_played(self) -> int:
        return self.match.rounds - self.afk

    @property
    def clutches(self) -> int:
        # round wins on v[N] situations
        return sum(
            self.clutch_v1,
            self.clutch_v2,
            self.clutch_v3,
            self.clutch_v4,
            self.clutch_v5,
        )

    @property
    def shots_hit(self) -> int:
        # all shots fired that hit a target
        return sum(self.head_shots, self.chest_shots, self.lef_shots)

    @property
    def frag(self) -> int:
        return f'{self.kills} / {self.deaths} / {self.assists}'

    @property
    def adr(self) -> str:
        # average damage per round
        if self.rounds_played > 0:
            return float('{:0.2f}'.format(self.damage / self.rounds_played))
        return float(0)

    @property
    def kdr(self):
        # kill/death ratio
        if self.deaths > 0:
            return float('{:0.2f}'.format(self.kills / self.deaths))
        return float('{:0.2f}'.format(self.kills))

    @property
    def kda(self):
        # kill/death/assists ratio
        if self.deaths > 0:
            return float('{:0.2f}'.format((self.kills + self.assists) / self.deaths))
        return float('{:0.2f}'.format(self.kills + self.assists))

    @property
    def ahk(self):
        # average headshot kills per shot
        if self.shots_fired > 0:
            return float('{:0.2f}'.format(self.hs_kills / self.shots_fired))
        return float(0)

    @property
    def ahr(self):
        # average headshots per round
        if self.shots_fired > 0:
            return float('{:0.2f}'.format(self.head_shots / self.match.rounds))
        return float(0)

    @property
    def accuracy(self):
        # average accuracy per shot
        if self.shots_fired > 0:
            return float('{:0.2f}'.format(self.hit_shots / self.shots_fired))
        return float(0)

    @property
    def head_accuracy(self):
        # head accuracy
        if self.hit_shots > 0:
            return float('{:0.2f}'.format(self.head_shots / self.hit_shots))
        return float(0)

    @property
    def chest_accuracy(self):
        # chest accuracy
        if self.hit_shots > 0:
            return float('{:0.2f}'.format(self.chest_shots / self.hit_shots))
        return float(0)

    @property
    def leg_accuracy(self):
        # leg accuracy
        if self.hit_shots > 0:
            return float('{:0.2f}'.format(self.leg_shots / self.hit_shots))
        return float(0)
