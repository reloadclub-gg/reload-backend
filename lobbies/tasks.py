import time

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.websocket import ws_update_user

from . import models
from .websocket import ws_queue_tick, ws_update_lobby

User = get_user_model()


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


@shared_task
def end_player_restriction(user_id: int):
    user = User.objects.get(pk=user_id)
    lobby = user.account.lobby
    ws_update_lobby(lobby)
    ws_update_user(user)
