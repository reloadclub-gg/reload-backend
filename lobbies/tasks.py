import time

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from . import models
from .websocket import ws_queue_tick


@shared_task
def clear_dodges():
    players = models.Player.get_all()
    last_week = timezone.now() - timezone.timedelta(weeks=1)
    for player in players:
        if player.latest_dodge and player.latest_dodge <= last_week:
            player.dodge_clear()


@shared_task
def queue_tick(lobby_id: int):
    lobby = models.Lobby(owner_id=lobby_id)
    if lobby.queue:
        ws_queue_tick(lobby)
        if not settings.TEST_MODE:
            time.sleep(1)
            queue_tick(lobby_id)
