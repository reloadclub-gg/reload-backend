from typing import List

from celery import shared_task
from django.contrib.auth import get_user_model

from lobbies.models import Lobby
from websocket import controller

User = get_user_model()


@shared_task
def user_status_change_task(user_id: int):
    user = User.objects.get(pk=user_id)
    controller.user_status_change(user)


@shared_task
def lobby_update_task(lobbies_ids: List[int]):
    lobbies = [Lobby(owner_id=lobby_id) for lobby_id in lobbies_ids]
    controller.lobby_update(lobbies)
