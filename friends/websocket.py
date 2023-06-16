from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from websocket.utils import ws_send

from .api import schemas

User = get_user_model()


def ws_friend_update(user: User) -> schemas.FriendSchema:
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

    Payload:
    friends.api.schemas.FriendSchema: object
    """
    online_friends_ids = [account.user.id for account in user.account.online_friends]
    payload = schemas.FriendSchema.from_orm(user.account).dict()
    return async_to_sync(ws_send)('friends/update', payload, groups=online_friends_ids)
