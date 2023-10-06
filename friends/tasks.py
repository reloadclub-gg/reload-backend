from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils.translation import activate
from django.utils.translation import gettext as _

from core.redis import redis_client_instance as cache
from notifications.websocket import ws_new_notification

from .websocket import ws_friend_update_or_create

User = get_user_model()


@shared_task
def notify_friends_about_signup(user_id: int, lang: str = None):
    lang and activate(lang)

    user = User.objects.get(pk=user_id)
    for friend in user.account.get_online_friends():
        notification = friend.notify(
            _('Your friend {} just joined ReloadClub!').format(user.account.username),
            from_user_id=user.id,
        )
        ws_new_notification(notification)


@shared_task
def add_user_to_friends_friendlist(user_id: int):
    user = User.objects.get(pk=user_id)
    for friend in user.account.get_online_friends():
        cache.sadd(f'__friendlist:user:{friend.user.id}', user.id)


@shared_task
def send_user_update_to_friendlist(user_id: int, action: str = 'update'):
    user = User.objects.get(pk=user_id)
    ws_friend_update_or_create(user, action)
