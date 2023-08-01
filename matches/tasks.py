import requests
from celery import shared_task
from django.conf import settings


@shared_task
def mock_fivem_match_start(match_id: int):
    if settings.ENVIRONMENT == settings.LOCAL:
        url = f'http://django:8000/api/matches/{match_id}/'
        r = requests.patch(
            url,
            json={'status': 'running'},
        )
        print(r)
