from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from websocket.utils import ws_send

from . import models
from .api import schemas

User = get_user_model()


def ws_delete_invite(invite: models.LobbyInvite, status: str):
    """
    Sends a delete invite event to client. The status represents
    what happened to that invite.

    Cases:
    - User accepts an invite.
    - User refuses an invite.

    Payload:
    lobbies.api.schemas.LobbyInviteWebsocketSchema: object
    """
    payload = schemas.LobbyInviteWebsocketSchema.from_orm(
        {
            'invite': invite,
            'status': status,
        }
    )

    return async_to_sync(ws_send)(
        'invites/delete',
        payload,
        groups=[invite.to_id, invite.from_id],
    )


def ws_create_invite(invite: models.LobbyInvite):
    """
    Triggered when a user receives an invitation to join a lobby.

    Cases:
    - User gets invited by another user to join a different lobby.

    Payload:
    lobbies.api.schemas.LobbyInviteSchema: object
    """
    payload = schemas.LobbyInviteSchema.from_orm(invite).dict()

    return async_to_sync(ws_send)(
        'invites/create',
        payload,
        groups=[invite.to_id],
    )


def ws_update_player(lobby: models.Lobby, user: User, action: str):
    """
    Triggered when a user joins or leaves a lobby. Is sent to all other
    lobby players.

    Cases:
    - User leaves a lobby that has another players on it.
    - User joins a lobby.

    Payload:
    lobbies.api.schemas.LobbyPlayerWebsocketUpdate: object
    """
    groups = [
        lobby_player_id
        for lobby_player_id in lobby.players_ids
        if lobby_player_id != user.id
    ]
    action = 'player_join' if action == 'join' else 'player_leave'
    payload = schemas.LobbyPlayerWebsocketUpdate.from_orm(
        {
            'player': user,
            'lobby': lobby,
        }
    )

    return async_to_sync(ws_send)(
        f'lobbies/{action}',
        payload,
        groups=groups or [],
    )


def ws_update_lobby(lobby: models.Lobby):
    """
    Triggered everytime a lobby gets updated.

    Cases:
    - Lobby starts queue.
    - Lobby cancel queue.

    Payload:
    lobbies.api.schemas.LobbySchema: object
    """
    payload = schemas.LobbySchema.from_orm(lobby).dict()
    return async_to_sync(ws_send)(
        'lobbies/update',
        payload,
        groups=lobby.players_ids,
    )
