from collections.abc import Callable
from functools import wraps

from django.contrib.auth import get_user_model
from ninja.errors import HttpError

from ..models import Lobby

User = get_user_model()


def is_lobby_owner(user: User, lobby_id: int) -> bool:
    lobby = Lobby(owner_id=lobby_id)

    return user.id == lobby.owner_id


def is_lobby_participant(user: User, lobby_id: int) -> bool:
    lobby = Lobby(owner_id=lobby_id)

    return user.id in lobby.players_ids


def owner_required(f: Callable) -> Callable:
    """
    Decorator for routes that require a lobby owner.
    The `is_lobby_owner` field set as `True` means the user is owner
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        request = args[0]
        lobby_id = kwds.get('lobby_id')

        if is_lobby_owner(request.user, lobby_id):
            return f(*args, **kwds)

        raise HttpError(401, 'User must be owner to perfom this action')

    return wrapper


def participant_required(f: Callable) -> Callable:
    """
    Decorator for routes that require a lobby participant.
    The `is_lobby_participant` field set as `True` means the user is participant
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        request = args[0]
        lobby_id = args[1]

        if is_lobby_participant(request.user, lobby_id):
            return f(*args, **kwds)

        raise HttpError(401, 'User must be owner to perfom this action')

    return wrapper
