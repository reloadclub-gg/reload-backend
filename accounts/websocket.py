from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

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
