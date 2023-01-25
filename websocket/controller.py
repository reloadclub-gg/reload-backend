from typing import List

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from accounts.api.schemas import FriendAccountSchema
from matchmaking.api.schemas import LobbyInviteSchema, LobbySchema
from matchmaking.models import Lobby, LobbyInvite

from .utils import ws_send

User = get_user_model()


def user_status_change(user: User):
    """
    Event called when a user change its status, eg. online to offline.
    Then we dispatch a ws message to his online friends so they can
    change that user status on client side.
    """
    online_friends_ids = [account.user.id for account in user.account.online_friends]
    payload = FriendAccountSchema.from_orm(user.account).dict()
    async_to_sync(ws_send)('ws_userStatusChange', payload, groups=online_friends_ids)


def friendlist_add(friend: User):
    """
    Event called when a user signup and finishes the account verifying process.
    This should get the brand new user to appear into his online friends list.
    """
    online_friends_ids = [account.user.id for account in friend.account.online_friends]
    payload = FriendAccountSchema.from_orm(friend.account).dict()
    async_to_sync(ws_send)('ws_friendlistAdd', payload, groups=online_friends_ids)


def lobby_update(lobbies: List[Lobby]):
    for lobby in lobbies:
        payload = LobbySchema.from_orm(lobby).dict()
        groups = lobby.players_ids
        async_to_sync(ws_send)('ws_lobbyUpdate', payload, groups=groups)


def lobby_player_invite(invite: LobbyInvite):
    """
    Event called when a player invites other to lobby.
    """
    payload = LobbyInviteSchema.from_orm(invite).dict()
    async_to_sync(ws_send)('ws_lobbyInviteReceived', payload, groups=[invite.to_id])


def lobby_player_refuse_invite(invite: LobbyInvite):
    """
    Event called when a player refuse invite to entry lobby.
    """
    payload = LobbyInviteSchema.from_orm(invite).dict()
    async_to_sync(ws_send)('ws_refuseInvite', payload, groups=[invite.from_id])
