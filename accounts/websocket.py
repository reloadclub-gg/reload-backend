from asgiref.sync import async_to_sync

from websocket.utils import ws_send


def ws_update_lobby_id(user_id: int, lobby_id: int):
    """
    Triggered everytime a user moves from one lobby to another.
    This is sent to the user who moved.

    Cases:
    - User accepts an invite to join some lobby, leaving current lobby.
    - User leaves current lobby and returns to its original lobby.
    - Lobby owner leaves its lobby, leaving that lobby with another owner,
    thus, another lobby as well. In this case, all users from that lobby get this update.

    Payload:
    int

    Actions:
    - user/update_lobby_id
    """
    return async_to_sync(ws_send)(
        'user/update_lobby_id',
        lobby_id,
        groups=[user_id],
    )
