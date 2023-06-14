from asgiref.sync import async_to_sync

from websocket.utils import ws_send


def ws_update_lobby_id(user_id: int, lobby_id: int):
    return async_to_sync(ws_send)(
        'user/update_lobby_id',
        lobby_id,
        groups=[user_id],
    )
