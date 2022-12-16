from ..models import Lobby
from ninja.errors import HttpError


def lobby_remove(request_user_id: int, lobby_id: int, user_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    if request_user_id not in lobby.players_ids or user_id not in lobby.players_ids:
        raise HttpError(400, 'users is not in this lobby')

    if request_user_id != lobby.owner_id:
        raise HttpError(400, 'user is not owner this lobby')

    Lobby.move(user_id, to_lobby_id=user_id)

    return lobby
