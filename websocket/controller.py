from asgiref.sync import async_to_sync

from django.contrib.auth import get_user_model

from accounts.api.schemas import FriendAccountSchema
from .utils import ws_send

User = get_user_model()


def user_status_change(user: User):
    online_friends_ids = [account.user.id for account in user.account.online_friends]
    payload = FriendAccountSchema.from_orm(user.account).dict()
    async_to_sync(ws_send)('ws_userStatusChange', payload, groups=online_friends_ids)


def friendlist_add(friend: User):
    online_friends_ids = [account.user.id for account in friend.account.online_friends]
    payload = FriendAccountSchema.from_orm(friend.account).dict()
    async_to_sync(ws_send)('ws_friendlistAdd', payload, groups=online_friends_ids)
