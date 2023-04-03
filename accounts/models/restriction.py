from __future__ import annotations

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from .account import Account


class Report(models.Model):
    class Subject(models.IntegerChoices):
        HATE_SPEECH = 0
        CHAT_ABUSE = 1
        REPORT_ABUSE = 2
        BAD_CONDUCT = 3
        ANTI_GAME = 4
        ACCOUNT_SHARING = 5
        CHEATING = 6

    owner = models.ForeignKey(Account, on_delete=models.CASCADE)
    target = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name='reported_set'
    )
    subject = models.TextField(choices=Subject.choices)
    create_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        already_exists = Report.objects.filter(
            owner=self.owner,
            target=self.target,
            subject=self.subject,
            create_date__month__gte=timezone.now().month,
            create_date__year__gte=timezone.now().year,
        )

        if not already_exists:
            with transaction.atomic():
                self.target.report_points += 1
                self.target.save()
                super().save(*args, **kwargs)


class ReportAnalysis(models.Model):
    analyst = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
    )
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name='analysis_set'
    )
    create_date = models.DateTimeField(auto_now_add=True)
    restriction_time = models.IntegerField(null=True, help_text=_('In hours.'))
    comments = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            self.account.report_points = 0
            self.account.save()
            super().save(*args, **kwargs)
