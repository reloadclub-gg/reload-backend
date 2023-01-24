from django.contrib.auth import get_user_model
from ninja.errors import HttpError

from websocket import controller as ws_controller

from ..models import Lobby, LobbyException, LobbyInvite, LobbyInviteException, Team

User = get_user_model()


def lobby_remove_player(lobby_id: int, user_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    Lobby.move(user_id, to_lobby_id=user_id)
    ws_controller.lobby_update(lobby)

    user = User.objects.get(pk=user_id)
    ws_controller.user_status_change(user)

    return lobby


def lobby_invite(lobby_id: int, from_user_id: int, to_user_id: int) -> LobbyInvite:
    lobby = Lobby(owner_id=lobby_id)

    try:
        invite = lobby.invite(from_user_id, to_user_id)
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
    lobby_id: int, lobby_type: str, lobby_mode: int
) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

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


def set_public(lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)
    lobby.set_public()
    ws_controller.lobby_update(lobby)

    return lobby


def set_private(lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)
    lobby.set_private()
    ws_controller.lobby_update(lobby)

    return lobby


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

    user = User.objects.get(pk=lobby_id)
    ws_controller.lobby_update(lobby)
    ws_controller.user_status_change(user)

    team = Team.find(lobby)
    if not team:
        Team.build(lobby)

    return lobby


def lobby_cancel_queue(lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)
    lobby.cancel_queue()

    return lobby
