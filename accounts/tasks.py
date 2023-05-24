from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.redis import RedisClient
from websocket.controller import (
    lobby_update,
    user_lobby_invites_expire,
    user_status_change,
)

from .models import UserLogin

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


@shared_task
def decr_level_from_inactivity():
    """
    Task that checks daily for all inactive users
    and decr their level based on how many days
    he is inactive.
    """
    last_login = (
        UserLogin.objects.filter(
            user__is_active=True,
        )
        .order_by('timestamp')
        .last()
    )

    inactivity_limit = timezone.now() - timezone.timedelta(days=90)
    if last_login and last_login.timestamp < inactivity_limit:
        user = last_login.user
        if hasattr(user, 'account'):
            if user.account.is_verified:
                if user.account.level > 0:
                    user.account.level -= 1
                user.account.level_points = 0
                user.account.save()
