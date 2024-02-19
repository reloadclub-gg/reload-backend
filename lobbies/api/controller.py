from typing import List

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja.errors import AuthenticationError, Http404, HttpError

from accounts.websocket import ws_update_status_on_friendlist, ws_update_user
from core.websocket import ws_create_toast

from .. import websocket
from ..models import Lobby, LobbyException, LobbyInvite, LobbyInviteException
from . import schemas
from .schemas import LobbyInviteCreateSchema

User = get_user_model()


def accept_invite(user: User, invite_id: int) -> dict:
    try:
        invite = LobbyInvite.get(invite_id)
    except LobbyInviteException as exc:
        raise Http404(exc)

    if user.id != invite.to_player_id:
        raise AuthenticationError()

    try:
        new_lobby = Lobby.get(invite.lobby_id)
    except LobbyException as exc:
        raise Http404(exc)

    try:
        f_lobby, t_lobby, r_lobby = Lobby.move_player(user.id, new_lobby.owner_id)
    except LobbyException as exc:
        raise HttpError(400, exc)

    websocket.ws_delete_invite(invite, 'accepted')
    invite.delete()

    websocket.ws_update_lobby(f_lobby)
    websocket.ws_update_lobby(t_lobby)
    if r_lobby:
        websocket.ws_update_lobby(r_lobby)

    user.status = User.Status.TEAMING
    user.save()

    return {'status': 'accepted'}


def refuse_invite(user: User, invite_id: str) -> dict:
    try:
        invite = LobbyInvite.get(invite_id)
    except LobbyInviteException as exc:
        raise Http404(exc)

    if user.id != invite.to_player_id:
        raise AuthenticationError()

    try:
        lobby = Lobby.get(invite.lobby_id)
    except LobbyException as exc:
        raise Http404(exc)

    websocket.ws_delete_invite(invite, 'accepted')
    invite.delete()
    websocket.ws_update_lobby(lobby)
    return {'status': 'refused'}


def create_invite(user: User, payload: LobbyInviteCreateSchema) -> LobbyInvite:

    try:
        lobby = Lobby.get(payload.lobby_id)
    except LobbyException as exc:
        raise Http404(exc)

    if user.id != payload.from_user_id or user.id not in lobby.players_ids:
        raise AuthenticationError()

    try:
        invite = LobbyInvite.create(
            payload.lobby_id,
            payload.from_user_id,
            payload.to_user_id,
        )
    except LobbyException as exc:
        raise HttpError(400, exc)

    websocket.ws_create_invite(invite)
    websocket.ws_update_lobby(lobby)
    return invite


def update_player(
    user: User,
    lobby_id: int,
    payload: schemas.LobbyPlayerUpdateSchema,
) -> Lobby:
    try:
        lobby = Lobby.get(lobby_id)
        original_player_lobby = Lobby.get(payload.player_id)
    except LobbyException as exc:
        raise Http404(exc)

    if payload.action == 'kick':
        if user.id != lobby.owner_id:
            raise AuthenticationError()

    if payload.player_id == user.id and len(lobby.players_ids) == 1:
        raise HttpError(400, _('Can\'t left empty lobby.'))

    fl, tl, rl = Lobby.move_player(payload.player_id, payload.player_id)
    websocket.ws_update_lobby(lobby)
    websocket.ws_update_lobby(original_player_lobby)
    ws_create_toast(
        _('{} kicked you from lobby.').format(user.account.username),
        user_id=payload.player_id,
    )

    users_ids_to_update = [user.id]
    if len(fl.players_ids) == 1:
        users_ids_to_update.append(fl.owner_id)

    users = User.objects.filter(id__in=users_ids_to_update)
    for user in users:
        user.status = User.Status.ONLINE
        user.save()
        ws_update_user(user)
        ws_update_status_on_friendlist(user)

    return lobby


def update_queue(user: User, lobby_id: int, action: str) -> Lobby:
    available_actions = ['start', 'stop']
    if action not in available_actions:
        raise HttpError(400, _(f'Action must be {(" or ").join(available_actions)}.'))

    try:
        lobby = Lobby.get(lobby_id)
    except LobbyException as exc:
        raise Http404(exc)

    if user.id != lobby.owner_id:
        raise AuthenticationError(_('User is not the lobby owner.'))

    if action == 'start' and lobby.is_queued:
        raise HttpError(400, _('Lobby already queued.'))

    if action == 'stop' and not lobby.is_queued:
        raise HttpError(400, _('Lobby isn\'t queued.'))

    try:
        lobby.update_queue(action)
    except LobbyException as exc:
        raise HttpError(exc)

    User.objects.filter(id__in=lobby.players_ids).update(status=User.Status.QUEUED)

    return lobby


def update_mode(user: User, lobby_id: int, mode: str) -> Lobby:
    try:
        lobby = Lobby.get(lobby_id)
        lobby.update_mode(mode)
    except LobbyException as exc:
        if 'not found' in str(exc).lower():
            raise Http404(exc)
        else:
            raise HttpError(400, exc)

    websocket.ws_update_lobby(lobby)
    return lobby


def get_lobby(lobby_id: int) -> Lobby:
    try:
        return Lobby.get(lobby_id)
    except LobbyException as exc:
        raise Http404(exc)
