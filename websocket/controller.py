from typing import List

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from accounts.api.schemas import FriendAccountSchema
from lobbies.api.schemas import LobbySchema
from lobbies.models import Lobby

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
    return async_to_sync(ws_send)(
        'ws_userStatusChange', payload, groups=online_friends_ids
    )


def lobby_update(lobbies: List[Lobby]):
    """
    Called when a lobby has updates.
    """
    results = list()
    for lobby in lobbies:
        payload = LobbySchema.from_orm(lobby).dict()
        results.append(
            async_to_sync(ws_send)('ws_lobbyUpdate', payload, groups=lobby.players_ids)
        )
    return results
