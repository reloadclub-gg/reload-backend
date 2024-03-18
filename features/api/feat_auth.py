from collections.abc import Callable
from functools import wraps

from ninja.errors import AuthenticationError

from ..models import FeaturePreview


def feat_available(feat_name: str) -> Callable:
    """
    Decorator for routes that requires authenticated user to be an
    early adopter of some feature.
    """

    def dec(f: Callable):
        @wraps(f)
        def wrapper(*args, **kwds):
            request = args[0]

            try:
                FeaturePreview.objects.get(feature__name=feat_name, users=request.user)
            except FeaturePreview.DoesNotExist:
                raise AuthenticationError()

            return f(*args, **kwds)

        return wrapper

    return dec
