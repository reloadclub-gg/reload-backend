from collections.abc import Callable
from functools import wraps

from ninja.errors import HttpError
from ninja.security import HttpBearer

from django.contrib.auth import get_user_model

from .controller import login

User = get_user_model()


class AuthBearer(HttpBearer):
    def authenticate(self, request, token: str):
        """
        This is middleware to authenticate users. Is called everytime the client
        makes a new request. All logic goes into the `controller.login` method.

        :params request Request: The request object.
        :return: The login method result (Auth model or None).
        """
        return login(request, token)


def has_account(user: User) -> bool:
    """
    Return weather the received user has an account.
    """
    return hasattr(user, 'account') and user.account is not None


def is_verified(user: User) -> bool:
    """
    Return weather the received user has an account and is verified.
    """
    return has_account(user) and user.account.is_verified


def verified_required(f: Callable) -> Callable:
    """
    Authorization decorator for routes that require a verified account.
    The `is_verified` field set as `True` means the user has confirmed
    that he owns the email he entered on signup.
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        request = args[0]
        if is_verified(request.user):
            return f(*args, **kwds)
        raise HttpError(401, 'Unauthorized')

    return wrapper
