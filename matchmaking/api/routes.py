from ninja import Router
from accounts.api.auth import AuthBearer
from ..models import Lobby
from . import controller

router = Router(tags=['mm'])


@router.patch('lobby/leave/', auth=AuthBearer())
def lobby_leave(request):
    return Lobby.move(request.user.id, to_lobby_id=request.user.id)


@router.patch('lobby/set-public/', auth=AuthBearer())
def lobby_set_public(request):
    return request.user.account.lobby.set_public()


@router.patch('lobby/set-private/', auth=AuthBearer())
def lobby_set_private(request):
    return request.user.account.lobby.set_private()


@router.patch('lobby/{lobby_id}/remove-player/{user_id}/', auth=AuthBearer())
def lobby_remove(request, lobby_id: int, user_id: int):
    return controller.lobby_remove(
        request_user_id=request.user.id, lobby_id=lobby_id, user_id=user_id
    )


@router.post('lobby/{lobby_id}/invite-player/{player_id}/', auth=AuthBearer())
def lobby_invite(request, lobby_id: int, player_id: int):
    return controller.lobby_invite(
        user=request.user, lobby_id=lobby_id, player_id=player_id
    )


@router.patch('lobby/{lobby_id}/accept-invite/', auth=AuthBearer())
def lobby_accept_invite(request, lobby_id: int):
    return controller.lobby_accept_invite(request.user, lobby_id)


@router.patch('lobby/{lobby_id}/refuse-invite/', auth=AuthBearer())
def lobby_refuse_invite(request, lobby_id: int):
    return controller.lobby_refuse_invite(request.user, lobby_id)
