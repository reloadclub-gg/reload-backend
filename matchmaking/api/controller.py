from ninja.errors import HttpError
from django.contrib.auth import get_user_model
from ..models import Lobby

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

    if user.account.lobby.id != lobby.id:
        raise HttpError(400, 'User must be owner to perfom this action')

    if player_id in lobby.invites:
        raise HttpError(400, 'Player id has already been invited')

    if player_id in lobby.players_ids:
        raise HttpError(400, 'User already in lobby')

    lobby.invite(player_id)

    return lobby


def lobby_accept_invite(user: User, lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)

    if user.id not in lobby.invites:
        raise HttpError(400, 'Player id has not been invited')

    if user.id in lobby.players_ids:
        lobby.delete_invite(user.id)
    else:
        lobby.move(user.id, lobby_id)

    return lobby


def lobby_refuse_invite(user: User, lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)

    if user.id not in lobby.invites:
        raise HttpError(400, 'Player id has not been invited')

    lobby.delete_invite(user.id)

    return lobby
