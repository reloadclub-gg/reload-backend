from collections.abc import Callable
from functools import wraps

from django.contrib.auth import get_user_model
from ninja.errors import AuthenticationError

from ..models import Lobby

User = get_user_model()


def owner_required(f: Callable) -> Callable:
    """
    Decorator for routes that requires the authenticated user
    to be the lobby owner.
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        request = args[0]
        lobby_id = kwds.get('lobby_id')

        if Lobby.is_owner(lobby_id, request.user.id):
            return f(*args, **kwds)

        raise AuthenticationError()

    return wrapper


def participant_required(f: Callable) -> Callable:
    """
    Decorator for routes that requires the authenticated user
    to be a lobby participant.
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        request = args[0]
        lobby_id = kwds.get('lobby_id')
        lobby = Lobby(owner_id=lobby_id)

        if request.user.id in lobby.players_ids:
            return f(*args, **kwds)

        raise AuthenticationError()

    return wrapper
