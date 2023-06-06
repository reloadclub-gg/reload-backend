from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from websocket.utils import ws_send

from . import models
from .api import schemas

User = get_user_model()


def get_invite(invite_id: str) -> models.LobbyInvite:
    try:
        int(invite_id.split(':')[0])
        int(invite_id.split(':')[1])
    except ValueError as e:
        raise e

    try:
        invite = models.LobbyInvite.get_by_id(invite_id)
    except models.LobbyInviteException as e:
        raise e

    return invite


def ws_delete_invite(invite_id: str):
    invite = get_invite(invite_id)
    payload = schemas.LobbyInviteSchema.from_orm(invite).dict()

    return async_to_sync(ws_send)(
        'invites/delete',
        payload,
        groups=[invite.to_id, invite.from_id],
    )


def ws_lobby_owner_change(lobby_id: int):
    lobby = models.Lobby(owner_id=lobby_id)
    payload = schemas.LobbySchema.from_orm(lobby).dict()

    return async_to_sync(ws_send)(
        'lobbies/owner_change',
        payload,
        groups=lobby.players_ids,
    )


# @shared_task
# def ws_player_leave() 'lobbies/player_leave'

# @shared_task
# def ws_player_join() 'lobbies/player_join'
