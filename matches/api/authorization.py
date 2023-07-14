from collections.abc import Callable
from functools import wraps

from django.conf import settings
from ninja.errors import AuthenticationError

from core.utils import get_ip_address

from .. import models


def whitelisted_required(f: Callable) -> Callable:
    """
    Decorator for routes that requires the authenticated user
    to be the lobby owner.
    """

    @wraps(f)
    def wrapper(*args, **kwds):
        if settings.DEBUG:
            return f(*args, **kwds)

        request = args[0]
        request_ip = get_ip_address(request)
        whitelisted_ips = models.Server.objects.all().values_list('ip', flat=True)

        if request_ip in whitelisted_ips:
            return f(*args, **kwds)

        raise AuthenticationError()

    return wrapper
