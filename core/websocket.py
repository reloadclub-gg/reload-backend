from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from websocket.utils import ws_send

from .api import schemas

User = get_user_model()


def ws_create_toast(user_id: int, content: str, variant: str = 'info'):
    """
    Sends a websocket to the client so it can show a toast
    to the user.

    Cases:
    - User got kicked from lobby.

    Payload:
    core.api.schemas.ToastSchema: object

    Actions:
    - toasts/create
    """
    payload = schemas.ToastSchema.from_orm(
        {
            'content': content,
            'variant': variant,
        }
    ).dict()

    return async_to_sync(ws_send)(
        'toasts/create',
        payload,
        groups=[user_id],
    )


def ws_maintenance(status: str):
    """
    Sends a websocket to all online users so they know that system is about to
    start or end a maintence window. Thus, all queues and invites are disabled while
    in the maintence window.

    Cases:
    - We're gonna run a deploy.

    Payload:
    null

    Actions:
    - maintenance/start
    - maintenance/end
    """
    available_statuses = ['start', 'end']
    if status not in available_statuses:
        raise ValueError(_('Invalid status.'))

    return async_to_sync(ws_send)(
        f'maintenance/{status}',
        None,
        groups=[user.id for user in User.online_users()],
    )


def ws_ping():
    """
    Sends a ping to all online users.

    Cases:
    null

    Payload:
    null

    Actions:
    - keep_alive/ping
    """
    return async_to_sync(ws_send)('keep_alive/ping', None)
