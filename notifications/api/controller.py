from typing import List

from ninja.errors import Http404

from notifications.models import Notification

from .schemas import NotificationUpdateSchema


def list(user) -> List[Notification]:
    return user.account.notifications


def detail(user, notification_id: int) -> Notification:
    user_notifications = user.account.notifications
    notification = next(
        (item for item in user_notifications if item.id == notification_id), None
    )
    if not notification:
        raise Http404()

    return notification


def read(user, notification_id: int, form: NotificationUpdateSchema) -> Notification:
    notification = detail(user, notification_id)

    if hasattr(form, 'read_date'):
        notification.mark_as_read()

    return notification


def read_all(user) -> List[Notification]:
    [item.mark_as_read() for item in user.account.notifications]
    return user.account.notifications
