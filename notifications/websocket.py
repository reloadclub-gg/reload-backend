from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from websocket.utils import ws_send

from .api.schemas import NotificationSchema
from .models import Notification

User = get_user_model()


def ws_new_notification(notification_id: int):
    notification = Notification.get_by_id(notification_id)
    payload = NotificationSchema.from_orm(notification).dict()

    return async_to_sync(ws_send)(
        'notifications/add',
        payload,
        groups=[notification.to_user_id],
    )
