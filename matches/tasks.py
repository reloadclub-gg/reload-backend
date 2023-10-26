from datetime import timedelta

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from . import models


@shared_task
def mock_fivem_match_start(match_id: int):
    if settings.ENVIRONMENT == settings.LOCAL:
        url = f'http://api:8000/api/matches/{match_id}/'
        r = requests.patch(
            url,
            json={'status': 'running'},
        )
        print(r)


@shared_task
def mock_fivem_match_cancel(match_id: int):
    if settings.ENVIRONMENT == settings.LOCAL:
        url = f'http://api:8000/api/matches/{match_id}/'
        r = requests.delete(
            url,
            json={'status': 'cancelled'},
        )
        print(r)


@shared_task
def delete_old_cancelled_matches():
    day_ago = timezone.now() - timedelta(days=1)

    return models.Match.objects.filter(
        status=models.Match.Status.CANCELLED,
        end_date__lt=day_ago,
    ).delete()
