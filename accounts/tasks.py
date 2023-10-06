from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.redis import redis_client_instance as cache
from friends.websocket import ws_friend_update_or_create
from lobbies.api.controller import handle_player_move
from lobbies.models import LobbyException
from lobbies.websocket import ws_expire_player_invites

from . import utils, websocket
from .models import Account, UserLogin

User = get_user_model()


@shared_task
def watch_user_status_change(user_id: int):
    """
    Task that watches for a user status change, eg. became offline.
    If user is in lobby, the lobby should be purged.
    """
    user = User.objects.get(pk=user_id)
    if not user.is_online:
        # Expiring player invites
        ws_expire_player_invites(user)

        # If user has an account and it is in a lobby, handle the player move
        try:
            if user.account.lobby:
                handle_player_move(user, user.id, delete_lobby=True)
        except (Account.DoesNotExist, LobbyException) as e:
            if isinstance(e, Account.DoesNotExist):
                pass
            else:
                raise e

        # Expiring user session
        user.auth.expire_session(seconds=0)

        # Update or create friend and send websocket logout message
        ws_friend_update_or_create(user)
        websocket.ws_user_logout(user.id)

        # Deleting user from friend list cache
        cache.delete(f'__friendlist:user:{user.id}')


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


@shared_task
def send_welcome_email(email_to: str):
    utils.send_welcome_mail(email_to)


@shared_task
def send_verify_email(email_to: str, username: str, verification_token: str):
    utils.send_verify_account_mail(
        email_to,
        username,
        verification_token,
    )


@shared_task
def send_inactivation_mail(email_to: str):
    utils.send_inactivation_mail(email_to)
