from ninja import Router
from ninja.errors import HttpError
from accounts.api.auth import AuthBearer
from ..models import Lobby

router = Router(tags=['mm'])


@router.patch('lobby/leave/', auth=AuthBearer())
def lobby_leave(request):
    return Lobby.move(request.user.id)


@router.patch('lobby/set-public/', auth=AuthBearer())
def lobby_set_public(request):
    return request.user.account.lobby.set_public()


@router.patch('lobby/set-private/', auth=AuthBearer())
def lobby_set_private(request):
    return request.user.account.lobby.set_private()


@router.patch('lobby/remove/', auth=AuthBearer())
def lobby_remove(request):
    if request.user.account.lobby.players_count == 1:
        raise HttpError(400, 'Only you are in the lobby')

    return request.user.account.lobby.move(request.user.id, remove=True)
