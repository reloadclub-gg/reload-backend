from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from websocket.utils import ws_send

from . import models
from .api import schemas

User = get_user_model()


def ws_friends_add(user: User, friend: User):
    """
    Triggered when a Friendship is accepted. We send this for both users (from and to).

    Cases:
    - User accepts a Friendship request.

    Payload:
    friends.api.schemas.FriendSchema: object

    Actions:
    - friends/create
    """

    user_payload = schemas.FriendSchema.from_orm(user.account).dict()
    friend_payload = schemas.FriendSchema.from_orm(friend.account).dict()

    results = [
        async_to_sync(ws_send)('friends/create', user_payload, groups=[friend.id]),
        async_to_sync(ws_send)('friends/create', friend_payload, groups=[user.id]),
    ]

    return results


def ws_friend_request(friendship: models.Friendship):
    """
    Triggered when a Friendship is requested.

    Cases:
    - User sends a friend request to another user.

    Payload:
    friends.api.schemas.FriendshipSchema: object

    Actions:
    - friends/request
    """

    payload = schemas.FriendshipSchema.from_orm(friendship).dict()
    return async_to_sync(ws_send)(
        'friends/request',
        payload,
        groups=[friendship.user_to.id],
    )


def ws_friend_remove(user: User, friend: User):
    """
    Triggered when a Friendship is over.

    Cases:
    - User removes a friend.

    Payload:
    friends.api.schemas.FriendSchema: object

    Actions:
    - friends/delete
    """

    user_payload = schemas.FriendSchema.from_orm(user.account).dict()
    friend_payload = schemas.FriendSchema.from_orm(friend.account).dict()

    results = [
        async_to_sync(ws_send)('friends/delete', user_payload, groups=[friend.id]),
        async_to_sync(ws_send)('friends/delete', friend_payload, groups=[user.id]),
    ]

    return results
