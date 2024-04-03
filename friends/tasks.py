from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.translation import activate, gettext as _
from django.utils import timezone

from core.redis import redis_client_instance as cache
from core.websocket import ws_create_toast
from notifications.websocket import ws_new_notification

from . import models, websocket

User = get_user_model()


@shared_task
def notify_friends_about_signup(user_id: int, lang: str = None):
    lang and activate(lang)

    user = User.objects.get(pk=user_id)
    for friend in user.account.get_online_friends():
        notification = friend.notify(
            _("Your friend {} just joined ReloadClub!").format(user.account.username),
            from_user_id=user.id,
        )
        ws_new_notification(notification)


@shared_task
def add_user_to_friends_friendlist(user_id: int):
    user = User.objects.get(pk=user_id)
    for friend in user.account.get_online_friends():
        cache.sadd(f"__friendlist:user:{friend.user.id}", user.id)


@shared_task
def expire_friend_request():
    max_age = timezone.now() - timedelta(hours=settings.FRIEND_REQUEST_MAX_AGE)
    expiring_requests = models.Friendship.objects.filter(
        accept_date__isnull=True,
        create_date__lte=max_age,
    )

    for request in expiring_requests:
        ws_create_toast(
            _(
                f"The friend request from {request.user_from.account.username} has expired."
            ),
            user_id=request.user_to.id,
        )
        ws_create_toast(
            _(f"The friend request to {request.user_to.account.username} has expired."),
            user_id=request.user_from.id,
        )
        websocket.ws_friend_request_expire(request)

    expiring_requests.delete()
