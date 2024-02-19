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

    Actions:
    - invites/delete
    """
    payload = schemas.LobbyInviteWebsocketSchema.from_orm(
        {
            'invite': invite,
            'status': status,
        }
    ).dict()

    return async_to_sync(ws_send)(
        'invites/delete',
        payload,
        groups=[invite.to_player_id, invite.from_player_id],
    )


def ws_create_invite(invite: models.LobbyInvite):
    """
    Triggered when a user receives an invitation to join a lobby.

    Cases:
    - User gets invited by another user to join a different lobby.

    Payload:
    lobbies.api.schemas.LobbyInviteSchema: object

    Actions:
    - invites/create
    """
    payload = schemas.LobbyInviteSchema.from_orm(invite).dict()

    return async_to_sync(ws_send)(
        'invites/create',
        payload,
        groups=[invite.to_player_id],
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

    Actions:
    - lobbies/player_join
    - lobbies/player_leave
    """
    groups = [
        lobby_player_id
        for lobby_player_id in lobby.players_ids
        if lobby_player_id != user.id
    ]
    action = 'player_join' if action == 'join' else 'player_leave'
    payload = schemas.LobbyPlayerWebsocketUpdate.from_orm(
        {
            'player': user.account,
            'lobby': lobby,
        }
    ).dict()

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

    Actions:
    - lobbies/update
    """
    payload = schemas.LobbySchema.from_orm(lobby).dict()
    return async_to_sync(ws_send)(
        'lobbies/update',
        payload,
        groups=lobby.players_ids,
    )


def ws_expire_player_invites(user: User, sent: bool = False, received: bool = False):
    """
    Triggered upon a player disconnection from websocket. This will clean both
    sent and received lobby invites from that player.

    Cases:
    - User logout.
    - User loses all sessions (disconnect from websocket).

    Payload:
    lobbies.api.schemas.LobbyInviteSchema: list

    Actions:
    - invites/expire
    """
    if sent:
        invites = models.LobbyInvite.get_by_player_id(user.id)
    elif received:
        invites = models.LobbyInvite.get_by_player_id(user.id, direction='to')
    else:
        invites = models.LobbyInvite.get_by_player_id(user.id, direction='both')

    results = list()
    for invite in invites:
        payload = schemas.LobbyInviteSchema.from_orm(invite).dict()
        results.append(
            async_to_sync(ws_send)(
                'invites/expire',
                payload,
                groups=[invite.to_player_id, invite.from_player_id],
            )
        )
        models.LobbyInvite.delete(invite)
    return results


def ws_queue_tick(lobby: models.Lobby):
    """
    Triggered every second for a queued lobby.

    Cases:
    - Queued lobby second tick.

    Payload:
    int

    Actions:
    - lobbies/queue_tick
    """
    return async_to_sync(ws_send)(
        'lobbies/queue_tick',
        lobby.queue_time,
        groups=lobby.players_ids,
    )


def ws_queue_start(lobby: models.Lobby):
    """
    This ws tells the client to restart its queue, as all players
    were marked as ready.

    Cases:
    - Triggered when a pre_match is cancelled by other lobbies.

    Payload:
    null

    Actions:
    - lobbies/queue_start
    """
    return async_to_sync(ws_send)(
        'lobbies/queue_start',
        None,
        groups=[lobby.owner_id],
    )
