from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class PlayerDodges(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    count = models.IntegerField(default=1)
    last_dodge_date = models.DateTimeField(auto_now=True)


class PlayerRestriction(models.Model):
    class Reason(models.TextChoices):
        DODGES = 'dodges'
        REPORTS = 'reports'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    reason = models.CharField(max_length=16, choices=Reason.choices)

    @property
    def countdown(self):
        return timedelta(self.end_date - timezone.now()).seconds
