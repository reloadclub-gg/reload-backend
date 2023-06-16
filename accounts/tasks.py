from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.redis import RedisClient
from friends.websocket import ws_friend_create_or_update
from lobbies.api.controller import player_move
from lobbies.websocket import ws_expire_player_invites

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
        ws_expire_player_invites(user)
        if user.account.lobby:
            player_move(user, user.id, delete_lobby=True)

        ws_friend_create_or_update(user)


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
