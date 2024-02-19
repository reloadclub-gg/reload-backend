from typing import List

from django.utils.translation import gettext as _
from ninja import Router
from ninja.errors import HttpError

from accounts.api.authentication import VerifiedRequiredAuth

from . import authorization, controller, schemas

router = Router(tags=['lobbies'])


@router.post(
    'invites/',
    auth=VerifiedRequiredAuth(),
    response={201: schemas.LobbyInviteSchema},
)
def invite_create(request, payload: schemas.LobbyInviteCreateSchema):
    return controller.create_invite(request.user, payload)


@router.delete(
    'invites/{invite_id}/',
    auth=VerifiedRequiredAuth(),
)
def invite_delete(request, invite_id: int, payload: schemas.LobbyInviteDeleteSchema):
    if payload.accept:
        return controller.accept_invite(request.user, invite_id)
    elif payload.refuse:
        return controller.refuse_invite(request.user, invite_id)
    else:
        return HttpError(400, _('Invite must be accepted or refused. Can\'t be none.'))


@router.patch(
    '{lobby_id}/players/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbySchema},
)
@authorization.owner_required
def player_update(request, lobby_id: int, payload: schemas.LobbyPlayerUpdateSchema):
    return controller.update_player(request.user, lobby_id, payload)


@router.patch(
    '{lobby_id}/queue/{action}',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbySchema},
)
@authorization.participant_required
def queue_update(request, lobby_id: int, action: str):
    return controller.update_queue(request.user, lobby_id, action)


@router.patch(
    '{lobby_id}/mode/{mode}',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbySchema},
)
@authorization.participant_required
def mode_update(request, lobby_id: int, mode: str):
    return controller.update_mode(request.user, lobby_id, mode)


@router.get(
    '{lobby_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.LobbySchema},
)
@authorization.participant_required
def detail(request, lobby_id: int):
    return controller.get_lobby(lobby_id)
