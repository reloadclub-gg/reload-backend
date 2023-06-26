from asgiref.sync import async_to_sync

from websocket.utils import ws_send

from .api import schemas


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
