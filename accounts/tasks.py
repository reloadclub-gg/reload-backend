from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model

from core.redis import RedisClient
from websocket.controller import (
    lobby_update,
    user_lobby_invites_expire,
    user_status_change,
)

cache = RedisClient()
logger = get_task_logger(__name__)
User = get_user_model()


@shared_task
def watch_user_status_change(
    user_id: int,
):  # int id because tasks cant serialize models
    """
    Task that watches for a user status change, eg. became offline.
    If user is in lobby, the lobby should be purged.
    """
    user = User.objects.get(pk=user_id)
    if not user.is_online:
        user_lobby_invites_expire(user)
        if user.account.lobby:
            new_lobby = user.account.lobby.move(user.id, user.id, remove=True)
            if new_lobby:
                lobby_update([new_lobby])

        user_status_change(user)
