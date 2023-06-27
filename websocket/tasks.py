from typing import List

from celery import shared_task
from django.contrib.auth import get_user_model

from lobbies.models import Lobby, LobbyInvite
from matches.models import Match
from notifications.models import Notification
from pre_matches.models import PreMatch
from websocket import controller

User = get_user_model()


@shared_task
def user_update_task(user_id: int):
    user = User.objects.get(pk=user_id)
    controller.user_update(user)


@shared_task
def user_status_change_task(user_id: int):
    user = User.objects.get(pk=user_id)
    controller.user_status_change(user)


@shared_task
def friendlist_add_task(friend_id: int, groups: List[int]):
    user = User.objects.get(pk=friend_id)
    controller.friendlist_add(user, groups)


@shared_task
def lobby_update_task(lobbies_ids: List[int]):
    lobbies = [Lobby(owner_id=lobby_id) for lobby_id in lobbies_ids]
    controller.lobby_update(lobbies)


@shared_task
def lobby_player_invite_task(lobby_id: int, invite_id: int):
    invite = LobbyInvite.get(lobby_id, invite_id)
    controller.lobby_player_invite(invite)


@shared_task
def lobby_player_refuse_invite_task(lobby_id: int, invite_id: int):
    lobby = Lobby(owner_id=lobby_id)
    invite = LobbyInvite.get(lobby_id, invite_id)
    lobby.delete_invite(invite_id)
    controller.lobby_player_refuse_invite(invite)


@shared_task
def lobby_invites_update_task(lobby_id: int, expired: bool = False):
    lobby = Lobby(owner_id=lobby_id)
    controller.lobby_invites_update(lobby, expired)


@shared_task
def user_lobby_invites_expire_task(user_id: int):
    user = User.objects.get(pk=user_id)
    controller.user_lobby_invites_expire(user)


@shared_task
def pre_match_task(pre_match_id: int):
    pre_match = PreMatch.get_by_id(pre_match_id)
    controller.pre_match(pre_match)


@shared_task
def match_cancel_task(pre_match_id: int):
    pre_match = PreMatch.get_by_id(pre_match_id)
    controller.match_cancel(pre_match)


@shared_task
def match_cancel_warn_task(lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)
    controller.match_cancel_warn(lobby)


@shared_task
def restart_queue_task(lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)
    controller.restart_queue(lobby)


@shared_task
def match_task(match_id: int):
    match = Match.objects.get(pk=match_id)
    controller.match(match)


@shared_task
def send_notification_task(notification_id: int):
    notification = Notification.get_by_id(notification_id)
    controller.new_notification(notification)
