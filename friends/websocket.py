from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from websocket.utils import ws_send

from .api import schemas

User = get_user_model()


def ws_status_update(user_id: int):
    user = User.objects.get(pk=user_id)
    online_friends_ids = [account.user.id for account in user.account.online_friends]
    payload = schemas.FriendSchema.from_orm(user.account).dict()
    return async_to_sync(ws_send)(
        'friends/status_update', payload, groups=online_friends_ids
    )
