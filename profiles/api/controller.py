from django.shortcuts import get_object_or_404

from accounts.models import Account


def detail(user_id: int = None, steamid: str = None, username: str = None) -> Account:
    query_args = {'user__is_active': True, 'is_verified': True}

    if user_id:
        query_args['user__id'] = user_id
    elif steamid:
        query_args['steamid'] = steamid
    elif username:
        query_args['username'] = username
    else:
        raise ValueError(
            "One of the parameters 'user_id', 'steamid', or 'username' must be provided"
        )

    return get_object_or_404(Account, **query_args)
