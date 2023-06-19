from asgiref.sync import async_to_sync

from websocket.utils import ws_send

from .api.schemas import NotificationSchema
from .models import Notification


def ws_new_notification(notification: Notification):
    """
    Triggered everytime a user gets notified.

    Cases:
    - Queues are down due to maintence.
    - A user friend from Steam just registered.

    Payload:
    notifications.api.schemas.NotificationSchema: object

    Actions:
    - notifications/add
    """
    payload = NotificationSchema.from_orm(notification).dict()

    return async_to_sync(ws_send)(
        'notifications/add',
        payload,
        groups=[notification.to_user_id],
    )
