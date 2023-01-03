from ninja import Router
from accounts.api.authentication import VerifiedRequiredAuth
from ..models import Lobby
from . import controller

router = Router(tags=['mm'])


@router.patch('lobby/leave/', auth=VerifiedRequiredAuth())
def lobby_leave(request):
    return Lobby.move(request.user.id, to_lobby_id=request.user.id)


@router.patch('lobby/set-public/', auth=VerifiedRequiredAuth())
def lobby_set_public(request):
    return controller.set_public(request.user)


@router.patch('lobby/set-private/', auth=VerifiedRequiredAuth())
def lobby_set_private(request):
    return controller.set_private(request.user)


@router.patch('lobby/{lobby_id}/remove-player/{user_id}/', auth=VerifiedRequiredAuth())
def lobby_remove(request, lobby_id: int, user_id: int):
    return controller.lobby_remove(
        request_user_id=request.user.id, lobby_id=lobby_id, user_id=user_id
    )


@router.post('lobby/{lobby_id}/invite-player/{player_id}/', auth=VerifiedRequiredAuth())
def lobby_invite(request, lobby_id: int, player_id: int):
    return controller.lobby_invite(
        user=request.user, lobby_id=lobby_id, player_id=player_id
    )


@router.patch('lobby/{lobby_id}/accept-invite/', auth=VerifiedRequiredAuth())
def lobby_accept_invite(request, lobby_id: int):
    return controller.lobby_accept_invite(request.user, lobby_id)


@router.patch('lobby/{lobby_id}/refuse-invite/', auth=VerifiedRequiredAuth())
def lobby_refuse_invite(request, lobby_id: int):
    return controller.lobby_refuse_invite(request.user, lobby_id)


@router.patch(
    'lobby/{lobby_id}/change-type/{lobby_type}/change-mode/{lobby_mode}/',
    auth=VerifiedRequiredAuth(),
)
def lobby_change_type_and_mode(
    request, lobby_id: int, lobby_type: str, lobby_mode: int
):
    return controller.lobby_change_type_and_mode(
        request.user, lobby_id, lobby_type, lobby_mode
    )


@router.patch('lobby/{lobby_id}/enter/', auth=VerifiedRequiredAuth())
def lobby_enter(request, lobby_id: int):
    return controller.lobby_enter(request.user, lobby_id)
