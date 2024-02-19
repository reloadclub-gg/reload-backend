from collections.abc import Callable
from functools import wraps

from django.contrib.auth import get_user_model
from ninja.errors import AuthenticationError, Http404

from ..models import Lobby, LobbyException

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
        try:
            lobby = Lobby.get(lobby_id)
        except LobbyException:
            raise Http404()

        if request.user.id in lobby.players_ids and lobby.owner_id == request.user.id:
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
        try:
            lobby = Lobby.get(lobby_id)
        except LobbyException:
            raise Http404()

        if request.user.id in lobby.players_ids:
            return f(*args, **kwds)

        raise AuthenticationError()

    return wrapper
