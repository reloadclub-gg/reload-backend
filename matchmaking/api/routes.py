from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller
from .authorization import owner_required, participant_required
from .schemas import LobbyInviteSchema, LobbySchema, PreMatchSchema

router = Router(tags=['mm'])


@router.patch('lobby/leave/', auth=VerifiedRequiredAuth(), response={200: LobbySchema})
def lobby_leave(request):
    return controller.lobby_leave(request.user)


@router.patch(
    'lobby/{lobby_id}/set-public/',
    auth=VerifiedRequiredAuth(),
    response={200: LobbySchema},
)
@owner_required
def lobby_set_public(request, lobby_id: int):
    return controller.set_public(lobby_id=lobby_id)


@router.patch(
    'lobby/{lobby_id}/set-private/',
    auth=VerifiedRequiredAuth(),
    response={200: LobbySchema},
)
@owner_required
def lobby_set_private(request, lobby_id: int):
    return controller.set_private(lobby_id=lobby_id)


@router.patch(
    'lobby/{lobby_id}/remove-player/{user_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: LobbySchema},
)
@owner_required
def lobby_remove_player(request, user_id: int, lobby_id: int):
    return controller.lobby_remove_player(user_id, lobby_id)


@router.post(
    'lobby/{lobby_id}/invite-player/{player_id}/',
    auth=VerifiedRequiredAuth(),
    response={201: LobbyInviteSchema},
)
@participant_required
def lobby_invite(request, lobby_id: int, player_id: int):
    return controller.lobby_invite(
        lobby_id=lobby_id, from_user_id=request.user.id, to_user_id=player_id
    )


@router.patch(
    'lobby/{lobby_id}/accept-invite/{invite_id}/',
    auth=VerifiedRequiredAuth(),
    response={201: LobbySchema},
)
def lobby_accept_invite(request, lobby_id: int, invite_id: str):
    return controller.lobby_accept_invite(request.user, lobby_id, invite_id)


@router.patch(
    'lobby/{lobby_id}/refuse-invite/{invite_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: LobbyInviteSchema},
)
def lobby_refuse_invite(request, lobby_id: int, invite_id: str):
    return controller.lobby_refuse_invite(lobby_id, invite_id)


@router.patch(
    'lobby/{lobby_id}/change-type/{lobby_type}/change-mode/{lobby_mode}/',
    auth=VerifiedRequiredAuth(),
    response={200: LobbySchema},
)
@owner_required
def lobby_change_type_and_mode(
    request, lobby_id: int, lobby_type: str, lobby_mode: int
):
    return controller.lobby_change_type_and_mode(lobby_id, lobby_type, lobby_mode)


@router.patch(
    'lobby/{lobby_id}/enter/', auth=VerifiedRequiredAuth(), response={200: LobbySchema}
)
def lobby_enter(request, lobby_id: int):
    return controller.lobby_enter(request.user, lobby_id)


@router.patch(
    'lobby/{lobby_id}/start-queue/',
    auth=VerifiedRequiredAuth(),
    response={200: LobbySchema},
)
@owner_required
def lobby_start_queue(request, lobby_id: int):
    return controller.lobby_start_queue(lobby_id)


@router.patch(
    'lobby/{lobby_id}/cancel-queue/',
    auth=VerifiedRequiredAuth(),
    response={200: LobbySchema},
)
@participant_required
def lobby_cancel_queue(request, lobby_id: int):
    return controller.lobby_cancel_queue(lobby_id)


@router.patch(
    'match/{match_id}/player-lock-in/',
    auth=VerifiedRequiredAuth(),
    response={200: PreMatchSchema},
)
def match_player_lock_in(request, match_id: str):
    return controller.match_player_lock_in(user=request.user, pre_match_id=match_id)


@router.patch(
    'match/{match_id}/player-ready/',
    auth=VerifiedRequiredAuth(),
    response={200: PreMatchSchema},
)
def match_player_ready(request, match_id: str):
    return controller.match_player_ready(user=request.user, pre_match_id=match_id)
