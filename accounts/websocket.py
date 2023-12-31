from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from friends.api.schemas import FriendSchema
from websocket.utils import ws_send

from .api import schemas

User = get_user_model()


def ws_update_user(user: User):
    """
    Triggered everytime a user is updated.

    Cases:
    - User moves from a lobby to another.
    - User change its e-mail.

    Payload:
    accounts.api.schemas.UserSchema: object

    Actions:
    - user/update
    """
    payload = schemas.UserSchema.from_orm(user).dict()
    return async_to_sync(ws_send)('user/update', payload, groups=[user.id])


def ws_user_logout(user_id: int):
    """
    Triggered everytime a user logs out.

    Cases:
    - User logout

    Payload:
    null

    Actions:
    - user/logout
    """

    return async_to_sync(ws_send)('user/logout', None, groups=[user_id])


def ws_update_status_on_friendlist(user: User):
    """
    Triggered everytime a user change its state. This sends an update
    about the user state to his online friends.

    Cases:
    - User logs in.
    - User joins a lobby friend leaving its old lobby empty.
    - User's current lobby starts queue.
    - User starts a match.
    - User is away due to being inactive for a period of time.
    - User doesn't refresh its sessions or expire them manually by logging out.
    - User friend just signup, verified and became online.

    Payload:
    friends.api.schemas.FriendSchema: object

    Actions:
    - friends/update
    """

    groups = [account.user.id for account in user.account.get_online_friends()]
    payload = FriendSchema.from_orm(user.account).dict()
    return async_to_sync(ws_send)('friends/update', payload, groups=groups)
