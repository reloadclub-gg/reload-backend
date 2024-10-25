import logging
from datetime import timedelta

import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from core.utils import send_mail

from . import models


@shared_task
def mock_fivem_match_start(match_id: int):
    if (
        settings.ENVIRONMENT != settings.LOCAL
        and not settings.FIVEM_MATCH_MOCKS_ON
        or settings.TEST_MODE
    ):
        return

    if settings.ENVIRONMENT == settings.LOCAL:
        url = f'{settings.DOCKER_SITE_URL}/api/matches/{match_id}/'
    else:
        url = f'{settings.SITE_URL}/api/matches/{match_id}/'

    r = requests.patch(
        url,
        json={'status': 'running'},
    )
    return r


@shared_task
def mock_fivem_match_cancel(match_id: int):
    if (
        settings.ENVIRONMENT != settings.LOCAL
        and not settings.FIVEM_MATCH_MOCKS_ON
        or settings.TEST_MODE
    ):
        return

    if settings.ENVIRONMENT == settings.LOCAL:
        url = f'{settings.DOCKER_SITE_URL}/api/matches/{match_id}/'
    else:
        url = f'{settings.SITE_URL}/api/matches/{match_id}/'
    r = requests.delete(
        url,
        json={'status': 'cancelled'},
    )
    return r


@shared_task
def delete_old_cancelled_matches():
    day_ago = timezone.now() - timedelta(days=1)

    return models.Match.objects.filter(
        status=models.Match.Status.CANCELLED,
        end_date__lt=day_ago,
    ).delete()


@shared_task
def send_server_almost_full_mail(name: str):
    server = models.Server.objects.get(name=name)
    running_matches = server.match_set.filter(
        status__in=[
            models.Match.Status.RUNNING,
            models.Match.Status.LOADING,
            models.Match.Status.WARMUP,
        ]
    ).count()

    send_mail(
        settings.ADMINS,
        'Servidor quase cheio',
        f'O servidor {server.name} ({server.ip}) está quase cheio: {running_matches}',
    )


@shared_task
def send_servers_full_mail():
    running_matches = models.Match.objects.filter(
        status__in=[
            models.Match.Status.RUNNING,
            models.Match.Status.LOADING,
            models.Match.Status.WARMUP,
        ]
    ).count()

    send_mail(
        settings.ADMINS,
        'Servidores cheios',
        f'Todos os servidores estão cheios. Total de partidas: {running_matches}',
    )


@shared_task
def remove_pending_loading_matches():
    matches = models.Match.objects.filter(
        status=models.Match.Status.LOADING,
        create_date__lt=timezone.now() - timedelta(seconds=10),
    )
    if len(matches) > 0:
        logging.warning(
            f'[remove_pending_loading_matches] {[match.id for match in matches]}'
        )
        matches.delete()
