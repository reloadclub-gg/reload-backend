from typing import List

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja.errors import AuthenticationError, Http404, HttpError

from friends.websocket import ws_status_update
from notifications.websocket import ws_new_notification

from .. import websocket
from ..models import Lobby, LobbyException, LobbyInvite, LobbyInviteException
from .schemas import LobbyUpdateSchema

User = get_user_model()


def player_move(user: User, lobby_id: int) -> Lobby:
    old_lobby = user.account.lobby
    new_lobby = Lobby(owner_id=lobby_id)

    try:
        remnants_lobby = Lobby.move(user.id, to_lobby_id=lobby_id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    if remnants_lobby:
        websocket.ws_lobby_owner_change(remnants_lobby.id)

        if new_lobby.id == old_lobby.id:
            ws_status_update(user.id)
            return new_lobby

    if old_lobby.players_count == 0 and new_lobby.players_count > 1:
        if not remnants_lobby:
            ws_status_update(user.id)
        ws_status_update(new_lobby.owner_id)

    if user.id != old_lobby.owner_id and old_lobby.players_count == 1:
        ws_status_update(old_lobby.owner_id)
    elif user.id == new_lobby.owner_id and new_lobby.players_count == 1:
        ws_status_update(user.id)

    return new_lobby


def get_lobby(lobby_id: int) -> Lobby:
    # TODO: check if lobby exists
    return Lobby(owner_id=lobby_id)


def get_user_invites(
    user: User,
    sent: bool = False,
    received: bool = False,
) -> List[LobbyInvite]:
    invites_sent = LobbyInvite.get_by_from_user_id(user.id)
    invites_received = LobbyInvite.get_by_to_user_id(user.id)

    if sent:
        return invites_sent

    if received:
        return invites_received

    return invites_sent + invites_received


def get_invite(user: User, invite_id: str) -> LobbyInvite:
    try:
        from_id = int(invite_id.split(':')[0])
        to_id = int(invite_id.split(':')[1])
    except:
        raise HttpError(422, _('Invalid invite id'))

    if user.id not in [from_id, to_id]:
        raise AuthenticationError()

    try:
        invite = LobbyInvite.get_by_id(invite_id)
    except LobbyInviteException as e:
        raise Http404(e)

    return invite


def accept_invite(user: User, invite_id: str):
    invite = get_invite(user, invite_id)
    if user.id != invite.to_id:
        raise AuthenticationError()

    current_lobby = user.account.lobby
    new_lobby = Lobby(owner_id=invite.lobby_id)

    if current_lobby.id == new_lobby.id:
        return

    websocket.ws_delete_invite(invite.id)

    inviter = User.objects.get(pk=invite.from_id)
    player_move(user, new_lobby.id)

    notification = inviter.account.notify(
        _(f'{user.account.username} accepted your invite and joined your group.'),
        user.id,
    )
    ws_new_notification(notification.id)


def refuse_invite(user: User, invite_id: str):
    invite = get_invite(user, invite_id)
    if user.id != invite.to_id:
        raise AuthenticationError()

    inviter = User.objects.get(pk=invite.from_id)

    notification = inviter.account.notify(
        _(f'{user.account.username} refused your invite.'),
        user.id,
    )
    ws_new_notification(notification.id)

    websocket.ws_delete_invite(invite.id)
    lobby = Lobby(owner_id=invite.lobby_id)
    lobby.delete_invite(invite.id)


def delete_player(user: User, lobby_id: int, player_id: int) -> Lobby:
    lobby = get_lobby(lobby_id)

    if player_id == user.id:
        if lobby.players_count == 1:
            return lobby

        return player_move(user, user.id)

    if user.id != lobby.owner_id:
        raise AuthenticationError()
    else:
        player = User.objects.get(pk=player_id)
        player_move(player, player.id)

    return lobby


def update_lobby(user: User, lobby_id: int, payload: LobbyUpdateSchema) -> Lobby:
    lobby = get_lobby(lobby_id)

    if payload.start_queue:
        if user.id != lobby.owner_id:
            raise AuthenticationError()

        try:
            lobby.start_queue()
        except LobbyException as e:
            raise HttpError(400, e)

        return lobby

    if payload.cancel_queue:
        lobby.cancel_queue()
        return lobby
