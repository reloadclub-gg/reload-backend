from collections.abc import Callable
from functools import wraps

from ninja.errors import AuthenticationError

from ..utils import is_feat_available_for_user


def feat_available(feat_name: str) -> Callable:
    """
    Decorator for routes that requires authenticated user to be an
    early adopter of some feature.
    """

    def dec(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwds):
            request = args[0]
            if not is_feat_available_for_user(feat_name, request.user):
                raise AuthenticationError()

            return f(*args, **kwds)

        return wrapper

    return dec
