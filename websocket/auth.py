from typing import List

from django.contrib.auth import get_user_model

from accounts.models import Auth
from accounts.tasks import watch_user_status_change
from core.utils import get_url_param

User = get_user_model()


class WSAuthConfig:
    CHECK_OFFLINE_COUNTDOWN: int = 15


def check_and_fetch_user(userq_qs: List[User]) -> User:
    if userq_qs.exists():
        if hasattr(userq_qs[0], 'account') and userq_qs[0].account.is_verified:
            return userq_qs[0]


def authenticate(scope: dict) -> User:
    """
    This is middleware to authenticate users on each websocket new connection.
    It checks if there is any existing user for the given auth token and increment
    that user session on Redis everytime he connects connects (e.g. multiple open browsers/tabs).

    :params scope dict: The websocket connection context.
    """
    token = get_url_param(scope.get('query_string'), 'token')
    auth = Auth.load(token)
    if not auth:
        return None

    user_qs = User.objects.filter(id=auth.user_id, is_active=True)
    user = check_and_fetch_user(user_qs)
    if user.auth.sessions_ttl > -1:
        user.add_session()
        user.auth.persist_session()

    return user


def disconnect(user):
    """
    This is middleware to disconnect users on each websocket connection close.
    It decrements user sessions count on Redis cache db. If this count became 0
    after the decrementing, we set an expire time. This is because if user refreshes
    the page, the connection will close when the refresh starts and open again when
    the refresh is done (considering that the user has the auth rights). So, while the
    user is refreshing, he has 0 sessions but he is not offline. A user is considered
    offline if there is no sesion entries for his `id` on Redis.

    :params user User: The user who will have his sessions count decreased.
    """
    if user.auth.sessions and user.auth.sessions > 0:
        user.auth.remove_session()
        if user.auth.sessions == 0:
            user.auth.expire_session()
            if hasattr(user, 'account') and user.account.is_verified:
                watch_user_status_change.apply_async(
                    (user.id,),
                    countdown=WSAuthConfig.CHECK_OFFLINE_COUNTDOWN,
                    serializer='json',
                )
