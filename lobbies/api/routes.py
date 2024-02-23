from typing import List

from django.utils.translation import gettext as _
from ninja import Router
from ninja.errors import HttpError

from accounts.api.authentication import VerifiedRequiredAuth

from . import authorization, controller, schemas

router = Router(tags=['lobbies'])


@router.get(
    'invites/',
    auth=VerifiedRequiredAuth(),
    response={200: List[schemas.LobbyInviteSchema]},
)
def invite_list(
    request,
    sent: bool = False,
    received: bool = False,
):
    return controller.get_user_invites(request.user, sent, received)


@router.post(
    'invites/',
    auth=VerifiedRequiredAuth(),
    response={201: schemas.LobbyInviteSchema},
)
def invite_create(request, payload: schemas.LobbyInviteCreateSchema):
    return controller.create_invite(request.user, payload)


@router.get(
    'invites/{invite_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbyInviteSchema},
)
def invite_detail(request, invite_id: str):
    return controller.get_invite(request.user, invite_id)


@router.delete(
    'invites/{invite_id}/',
    auth=VerifiedRequiredAuth(),
)
def invite_delete(request, invite_id: str, payload: schemas.LobbyInviteDeleteSchema):
    if payload.accept:
        return controller.accept_invite(request.user, invite_id)
    elif payload.refuse:
        return controller.refuse_invite(request.user, invite_id)
    else:
        return HttpError(400, _('Invite must be accepted or refused. Can\'t be none.'))


@router.delete(
    '{lobby_id}/players/{player_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbySchema},
)
@authorization.participant_required
def player_delete(request, lobby_id: int, player_id: int):
    return controller.delete_player(request.user, lobby_id, player_id)


@router.patch(
    '{lobby_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbySchema},
)
@authorization.participant_required
def update(request, lobby_id: int, payload: schemas.LobbyUpdateSchema):
    return controller.update_lobby(request.user, lobby_id, payload)


@router.patch(
    '{lobby_id}/players/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbySchema},
)
@authorization.participant_required
def player_update(request, lobby_id: int, payload: schemas.LobbyPlayerUpdateSchema):
    return controller.update_player(lobby_id, payload)


@router.get(
    '{lobby_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbySchema},
)
@authorization.participant_required
def detail(request, lobby_id: int):
    return controller.get_lobby(lobby_id)
