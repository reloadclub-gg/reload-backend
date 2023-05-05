from typing import List

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from accounts.api.schemas import FriendAccountSchema, UserSchema
from matches.api.schemas import MatchSchema
from matches.models import Match
from matchmaking.api.schemas import LobbyInviteSchema, LobbySchema, PreMatchSchema
from matchmaking.models import Lobby, LobbyInvite, PreMatch
from notifications.api.schemas import NotificationSchema

from .utils import ws_send

User = get_user_model()


def user_update(user: User):
    """
    Event called when a user gets updated and do not receive an API response
    so the client can update the user.
    """
    payload = UserSchema.from_orm(user).dict()
    return async_to_sync(ws_send)('ws_userUpdate', payload, groups=[user.id])


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


def friendlist_add(friend: User, groups: List[int]):
    """
    Event called when a user signup and finishes the account verifying process.
    This should get the brand new user to appear into his online friends list.
    """
    payload = FriendAccountSchema.from_orm(friend.account).dict()
    return async_to_sync(ws_send)('ws_friendlistAdd', payload, groups=groups)


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


def lobby_player_invite(invite: LobbyInvite):
    """
    Event called when a player invites other to lobby.
    """
    payload = LobbyInviteSchema.from_orm(invite).dict()
    return async_to_sync(ws_send)(
        'ws_lobbyInviteReceived', payload, groups=[invite.to_id]
    )


def lobby_player_refuse_invite(invite: LobbyInvite):
    """
    Event called when a player refuse invite to entry lobby.
    """
    payload = LobbyInviteSchema.from_orm(invite).dict()
    return async_to_sync(ws_send)('ws_refuseInvite', payload, groups=[invite.from_id])


def lobby_invites_update(lobby: Lobby, expired: bool = False):
    """
    Event called when an invite gets updated.
    If invite is expired we send an action to remove invite from user invites list.
    """
    results = list()
    for invite in lobby.invites:
        payload = LobbyInviteSchema.from_orm(invite).dict()
        action = 'ws_updateInvite' if not expired else 'ws_removeInvite'
        results.append(
            async_to_sync(ws_send)(
                action, payload, groups=[invite.to_id, invite.from_id]
            )
        )
    return results


def user_lobby_invites_expire(user: User):
    """
    Event called to remove all invites from a user.
    """
    invites = user.account.lobby_invites_sent + user.account.lobby_invites
    results = list()
    for invite in invites:
        payload = LobbyInviteSchema.from_orm(invite).dict()
        results.append(
            async_to_sync(ws_send)(
                'ws_removeInvite', payload, groups=[invite.to_id, invite.from_id]
            )
        )
    return results


def pre_match(pre_match: PreMatch):
    """
    This event is triggered to create or update a pre match on client.
    """
    payload = PreMatchSchema.from_orm(pre_match).dict()
    results = list()

    for player in pre_match.players:
        payload['user_ready'] = player in pre_match.players_ready
        results.append(
            async_to_sync(ws_send)('ws_preMatch', payload, groups=[player.id])
        )
    return results


def match_cancel(pre_match: PreMatch):
    """
    This event is triggered to cancel a pre match on client.
    """
    groups = [player.id for player in pre_match.players]
    return async_to_sync(ws_send)('ws_preMatchCancel', None, groups=groups)


def match_cancel_warn(lobby: Lobby):
    """
    We use this event to warn players from a lobby that didn't get ready on pre match.
    """
    return async_to_sync(ws_send)(
        'ws_preMatchCancelWarn', None, groups=lobby.players_ids
    )


def restart_queue(lobby: Lobby):
    """
    Event to request that ready lobbies get in the queue again. This usually happens
    after a pre match gets canceled.
    """
    return async_to_sync(ws_send)('ws_restartQueue', None, groups=lobby.players_ids)


def match(match: Match):
    """
    This event is triggered to create or update a match on client.
    """
    payload = MatchSchema.from_orm(match).dict()

    return async_to_sync(ws_send)(
        'ws_match',
        payload,
        groups=[match_player.user.id for match_player in match.players],
    )


def new_notification(notification):
    payload = NotificationSchema.from_orm(notification).dict()

    return async_to_sync(ws_send)(
        'ws_newNotification',
        payload,
        groups=[notification.to_user_id],
    )
