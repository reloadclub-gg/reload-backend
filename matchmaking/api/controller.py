from django.contrib.auth import get_user_model
from ninja.errors import HttpError

from websocket import controller as ws_controller

from ..models import Lobby, LobbyException, LobbyInvite, LobbyInviteException

User = get_user_model()


def lobby_remove_player(request_user_id: int, lobby_id: int, user_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    if request_user_id not in lobby.players_ids or user_id not in lobby.players_ids:
        raise HttpError(400, 'User must be in lobby to perform this action')

    if request_user_id != lobby.owner_id:
        raise HttpError(400, 'User must be owner to perform this action')

    Lobby.move(user_id, to_lobby_id=user_id)
    ws_controller.lobby_update(lobby)

    user = User.objects.get(pk=user_id)
    ws_controller.user_status_change(user)

    return lobby


def lobby_invite(user: User, lobby_id: int, player_id: int) -> LobbyInvite:
    lobby = Lobby(owner_id=lobby_id)

    try:
        invite = lobby.invite(user.id, player_id)
        ws_controller.lobby_player_invite(invite)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return invite


def lobby_accept_invite(user: User, lobby_id: int, invite_id: str) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    if user.id in lobby.players_ids:
        lobby.delete_invite(invite_id)
    else:
        try:
            lobby.move(user.id, lobby_id)
        except LobbyException as exc:
            raise HttpError(400, str(exc))

        ws_controller.lobby_update(lobby)
        ws_controller.user_status_change(user)

    return lobby


def lobby_refuse_invite(lobby_id: int, invite_id: str):
    lobby = Lobby(owner_id=lobby_id)

    try:
        invite = LobbyInvite.get(lobby_id, invite_id)
        ws_controller.lobby_player_refuse_invite(invite)
        lobby.delete_invite(invite_id)
    except (LobbyException, LobbyInviteException) as exc:
        raise HttpError(400, str(exc))

    return lobby


def lobby_change_type_and_mode(
    user: User, lobby_id: int, lobby_type: str, lobby_mode: int
) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    if user.account.lobby.id != lobby.owner_id:
        raise HttpError(400, 'User must be owner to perfom this action')

    try:
        lobby.set_type(lobby_type)
        lobby.set_mode(lobby_mode)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    ws_controller.lobby_update(lobby)

    return lobby


def lobby_enter(user: User, lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    try:
        Lobby.move(user.id, lobby_id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    ws_controller.lobby_update(lobby)
    ws_controller.user_status_change(user)

    return lobby


def set_public(user: User) -> Lobby:
    if user.account.lobby.owner_id != user.id:
        raise HttpError(400, 'User must be owner to perfom this action')

    user.account.lobby.set_public()
    ws_controller.lobby_update(user.account.lobby)

    return user.account.lobby


def set_private(user: User) -> Lobby:
    if user.account.lobby.owner_id != user.id:
        raise HttpError(400, 'User must be owner to perfom this action')

    user.account.lobby.set_private()
    ws_controller.lobby_update(user.account.lobby)

    return user.account.lobby


def lobby_leave(user: User) -> User:
    lobby = user.account.lobby
    Lobby.move(user.id, to_lobby_id=user.id)

    ws_controller.lobby_update(lobby)

    user = User.objects.get(pk=user.id)
    ws_controller.user_status_change(user)

    return user


def lobby_start_queue(lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)

    try:
        lobby.start_queue()
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return lobby


def lobby_cancel_queue(lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)
    lobby.cancel_queue()

    return lobby
