import requests
from celery import shared_task
from django.conf import settings


@shared_task
def mock_fivem_match_start(match_id: int):
    if settings.ENVIRONMENT == settings.LOCAL:
        r = requests.patch(
            settings.SITE_URL + f'/match/{match_id}/',
            {'status': 'running'},
        )
        print(r)
