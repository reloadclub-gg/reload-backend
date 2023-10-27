from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth import get_user_model

from websocket.utils import ws_send

from .api import schemas

User = get_user_model()


def ws_friend_update_or_create(user: User, action: str = 'update'):
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
    - friends/create
    """
    if action not in ['update', 'create']:
        raise ValueError('action param should be "update" or "create".')

    if not hasattr(user, 'account'):
        return

    if settings.DEBUG:
        groups = ['global']
    else:
        groups = [account.user.id for account in user.account.get_online_friends()]

    user.refresh_from_db()
    payload = schemas.FriendSchema.from_orm(user.account).dict()
    return async_to_sync(ws_send)(f'friends/{action}', payload, groups=groups)
