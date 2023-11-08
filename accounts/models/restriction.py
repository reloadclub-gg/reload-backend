from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class AccountReport(models.Model):
    class Subject(models.IntegerChoices):
        HATE_SPEECH = 0
        CHAT_ABUSE = 1
        REPORT_ABUSE = 2
        BAD_CONDUCT = 3
        ANTI_GAME = 4
        ACCOUNT_SHARING = 5
        CHEATING = 6

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='report_set',
    )
    target = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_received',
    )
    subject = models.IntegerField(choices=Subject.choices)
    datetime_created = models.DateTimeField(auto_now_add=True)
    report_points = models.PositiveIntegerField(default=0)
    comments = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        already_exists = AccountReport.objects.filter(
            reporter=self.reporter,
            target=self.target,
            subject=self.subject,
            datetime_created__month__gte=timezone.now().month,
            datetime_created__year__gte=timezone.now().year,
        )

        if not already_exists:
            super().save(*args, **kwargs)
