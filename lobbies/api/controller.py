from typing import List

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja.errors import AuthenticationError, Http404, HttpError

from accounts.websocket import ws_update_lobby_id
from friends.websocket import ws_friend_create_or_update

from .. import websocket
from ..models import Lobby, LobbyException, LobbyInvite, LobbyInviteException
from .schemas import LobbyInviteCreateSchema, LobbyUpdateSchema

User = get_user_model()


def handle_move_extra_websockets(
    old_lobby: Lobby,
    new_lobby: Lobby,
    user: User,
    delete_lobby: bool = False,
    has_remnants: bool = False,
):
    if old_lobby.players_count == 0 and new_lobby.players_count > 1:
        if not has_remnants:
            ws_friend_create_or_update(user)
        new_owner = User.objects.get(pk=new_lobby.owner_id)
        ws_friend_create_or_update(new_owner)

    if user.id != old_lobby.owner_id and old_lobby.players_count == 1:
        old_owner = User.objects.get(pk=old_lobby.owner_id)
        ws_friend_create_or_update(old_owner)
    elif user.id == new_lobby.owner_id and new_lobby.players_count == 1:
        ws_friend_create_or_update(user)

    if not delete_lobby:
        websocket.ws_update_player(old_lobby, user, 'leave')
        websocket.ws_update_player(new_lobby, user, 'join')


def player_move(user: User, lobby_id: int, delete_lobby: bool = False) -> Lobby:
    old_lobby = user.account.lobby
    new_lobby = Lobby(owner_id=lobby_id)

    try:
        remnants_lobby = Lobby.move(user.id, to_lobby_id=lobby_id, remove=delete_lobby)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    if not delete_lobby:
        ws_update_lobby_id(user.id, new_lobby.id)

    if remnants_lobby:
        for player_id in remnants_lobby.players_ids:
            ws_update_lobby_id(player_id, remnants_lobby.id)

        websocket.ws_update_player(remnants_lobby, user, 'leave')

        if new_lobby.id == old_lobby.id:
            ws_friend_create_or_update(user)
            return new_lobby

    handle_move_extra_websockets(
        old_lobby,
        new_lobby,
        user,
        delete_lobby=delete_lobby,
        has_remnants=bool(remnants_lobby),
    )

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
    except ValueError:
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
        return {'status': None}

    websocket.ws_delete_invite(invite, 'accepted')
    player_move(user, new_lobby.id)
    return {'status': 'accepted'}


def refuse_invite(user: User, invite_id: str):
    invite = get_invite(user, invite_id)
    if user.id != invite.to_id:
        raise AuthenticationError()

    websocket.ws_delete_invite(invite, 'refused')
    lobby = Lobby(owner_id=invite.lobby_id)
    lobby.delete_invite(invite.id)
    return {'status': 'refused'}


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

    elif payload.cancel_queue:
        lobby.cancel_queue()

    websocket.ws_update_lobby(lobby)
    return lobby


def create_invite(user: User, payload: LobbyInviteCreateSchema):
    lobby = get_lobby(payload.lobby_id)

    if user.id != payload.from_user_id or user.id not in lobby.players_ids:
        raise AuthenticationError()

    try:
        invite = lobby.invite(payload.from_user_id, payload.to_user_id)
    except LobbyException as exc:
        raise HttpError(400, exc)

    websocket.ws_create_invite(invite)
    return invite
