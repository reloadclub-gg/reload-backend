import datetime

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext as _

from core.redis import redis_client_instance as cache
from friends.websocket import ws_friend_update_or_create
from lobbies.api.controller import handle_player_move
from lobbies.models import Lobby, LobbyException
from lobbies.websocket import ws_expire_player_invites, ws_update_lobby
from pre_matches.api.controller import cancel_pre_match
from pre_matches.models import PreMatch, Team

from . import utils, websocket
from .models import UserLogin

User = get_user_model()


@shared_task
def watch_user_status_change(user_id: int):
    """
    Task that watches for a user status change, eg. became offline.
    If user is in lobby, the lobby should be purged.
    """
    user = User.objects.get(pk=user_id)
    if not user.has_sessions:
        # Expiring player invites
        ws_expire_player_invites(user)

        # If user has an account
        if hasattr(user, 'account'):
            if user.account.lobby:
                lobby_id = user.account.lobby.id

                pre_match = PreMatch.get_by_player_id(user.id)
                if pre_match:
                    cancel_pre_match(
                        pre_match,
                        _('Match cancelled due to user not locked in.'),
                    )

                team = Team.get_by_lobby_id(lobby_id, fail_silently=True)
                if team:
                    team.remove_lobby(lobby_id)

            try:
                handle_player_move(user, user.id, delete_lobby=True)
            except LobbyException:
                if user.account.lobby:
                    ws_update_lobby(user.account.lobby)
                    Lobby.delete(user.account.lobby.id)

        # Expiring user session
        user.logout()
        user.refresh_from_db()

        # Update or create friend
        ws_friend_update_or_create(user)

        # Send websocket logout message
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


@shared_task
def send_invite_mail(email_to: str, from_username: str):
    utils.send_invite_mail(email_to, from_username)


@shared_task
def logout_inactive_users():
    date_from = timezone.now() - datetime.timedelta(days=1)
    logins = (
        UserLogin.objects.filter(
            timestamp__lte=date_from,
            user__status__in=User.online_statuses,
            user__is_staff=False,
        )
        .select_related('user')
        .distinct()
    )
    for login in logins:
        login.user.auth.expire_session(0)
        login.user.auth.refresh_token(0)
        watch_user_status_change(login.user.id)
