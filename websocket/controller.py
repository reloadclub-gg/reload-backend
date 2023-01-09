from asgiref.sync import async_to_sync

from django.contrib.auth import get_user_model

from accounts.api.schemas import FriendAccountSchema
from matchmaking.models import Lobby, LobbyInvite
from matchmaking.api.schemas import LobbySchema, InviteSchema
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


def lobby_player_leave(user: User, lobby: Lobby = None):
    """
    Event called when a player leaves a lobby.
    This should notify the others players on lobby that the user has left.
    """
    if not lobby:
        lobby = user.account.lobby

    lobby_players_ids = [id for id in lobby.players_ids if id != user.id]
    payload = LobbySchema.from_orm(lobby).dict()
    async_to_sync(ws_send)('ws_lobbyPlayerLeave', payload, groups=lobby_players_ids)


def lobby_update(lobby: Lobby):
    payload = LobbySchema.from_orm(lobby).dict()
    async_to_sync(ws_send)('ws_lobbyUpdate', payload, groups=lobby.players_ids)


def lobby_player_invite(invite: LobbyInvite):
    """
    Event called when a player invites other to lobby.
    """
    payload = InviteSchema.from_orm(invite).dict()
    async_to_sync(ws_send)('ws_newInvite', payload, groups=[invite.to_id])
