from django.shortcuts import get_object_or_404
from ninja.errors import Http404

from accounts.models import Account


def detail(user_id: int = None, steamid: str = None, username: str = None) -> Account:
    result = None

    if user_id:
        result = get_object_or_404(
            Account,
            user__id=user_id,
            user__is_active=True,
            is_verified=True,
        )
    elif steamid:
        result = get_object_or_404(
            Account,
            steamid=steamid,
            user__is_active=True,
            is_verified=True,
        )
    elif username:
        result = get_object_or_404(
            Account,
            username=username,
            user__is_active=True,
            is_verified=True,
        )

    if result:
        return result

    raise Http404()
