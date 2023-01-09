from ninja.errors import HttpError

from django.contrib.auth import get_user_model

from ..models import Lobby, LobbyException

User = get_user_model()


def lobby_remove(request_user_id: int, lobby_id: int, user_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    if request_user_id not in lobby.players_ids or user_id not in lobby.players_ids:
        raise HttpError(400, 'User must be in lobby to perform this action')

    if request_user_id != lobby.owner_id:
        raise HttpError(400, 'User must be owner to perform this action')

    Lobby.move(user_id, to_lobby_id=user_id)

    return lobby


def lobby_invite(user: User, lobby_id: int, player_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    try:
        invite = lobby.invite(user.id, player_id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return invite


def lobby_accept_invite(user: User, lobby_id: int, invite_id: str):
    lobby = Lobby(owner_id=lobby_id)

    if user.id in lobby.players_ids:
        lobby.delete_invite(invite_id)
    else:
        try:
            lobby.move(user.id, lobby_id)
        except LobbyException as exc:
            raise HttpError(400, str(exc))

    return lobby


def lobby_refuse_invite(lobby_id: int, invite_id: str):
    lobby = Lobby(owner_id=lobby_id)

    try:
        lobby.delete_invite(invite_id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return lobby


def lobby_change_type_and_mode(
    user: User, lobby_id: int, lobby_type: str, lobby_mode: int
):
    lobby = Lobby(owner_id=lobby_id)

    if user.account.lobby.id != lobby.owner_id:
        raise HttpError(400, 'User must be owner to perfom this action')

    try:
        lobby.set_type(lobby_type)
        lobby.set_mode(lobby_mode)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return lobby


def lobby_enter(user: User, lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)

    try:
        Lobby.move(user.id, lobby_id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return lobby


def set_public(user: User):
    if user.account.lobby.owner_id != user.id:
        raise HttpError(400, 'User must be owner to perfom this action')

    user.account.lobby.set_public()

    return user.account.lobby


def set_private(user: User):
    if user.account.lobby.owner_id != user.id:
        raise HttpError(400, 'User must be owner to perfom this action')

    user.account.lobby.set_private()

    return user.account.lobby
