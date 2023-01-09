from django.contrib.auth import get_user_model

from accounts.models import Auth
from accounts.tasks import watch_user_status_change
from core.redis import RedisClient
from core.utils import get_url_param
from matchmaking.models import Lobby

from .controller import user_status_change

User = get_user_model()
cache = RedisClient()


class WSAuthConfig:
    CHECK_OFFLINE_COUNTDOWN: int = 15


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

    def is_active_and_verified(user):
        return (
            user.exists()
            and hasattr(user[0], 'account')
            and user[0].account.is_verified()
        )

    user = User.objects.filter(id=auth.user_id, is_active=True)
    if not is_active_and_verified:
        return None

    user = user[0]
    notify_became_online = False

    if user.auth.sessions is None:
        notify_became_online = True

    user.auth.add_session()
    user.auth.persist_session()

    if notify_became_online:
        user_status_change(user)
        Lobby.create(user.id)

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
