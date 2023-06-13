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


def ws_delete_invite(invite_id: str, status: str):
    invite = get_invite(invite_id)
    payload = {
        'invite': schemas.LobbyInviteSchema.from_orm(invite).dict(),
        'status': status,
    }

    return async_to_sync(ws_send)(
        'invites/delete',
        payload,
        groups=[invite.to_id, invite.from_id],
    )


def ws_create_invite(invite_id: str):
    invite = get_invite(invite_id)
    payload = schemas.LobbyInviteSchema.from_orm(invite).dict()

    return async_to_sync(ws_send)(
        'invites/create',
        payload,
        groups=[invite.to_id],
    )


def ws_player_update(lobby_id: int, player_id: int, action: str):
    lobby = models.Lobby(owner_id=lobby_id)
    user = User.objects.get(pk=player_id)
    groups = [
        lobby_player_id
        for lobby_player_id in lobby.players_ids
        if lobby_player_id != player_id
    ]
    action = 'player_join' if action == 'join' else 'player_leave'
    payload = {
        'player': schemas.LobbyPlayerSchema.from_orm(user).dict(),
        'lobby': schemas.LobbySchema.from_orm(lobby).dict(),
    }

    return async_to_sync(ws_send)(
        f'lobbies/{action}',
        payload,
        groups=groups or [],
    )
