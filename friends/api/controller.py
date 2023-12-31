import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from ninja.errors import HttpError

from accounts.models import Account
from notifications.websocket import ws_new_notification

from .. import models, websocket
from . import schemas

User = get_user_model()


def list(user: User) -> dict:
    online_friends, offline_friends = [], []

    if settings.DEBUG:
        friends = Account.objects.filter(
            user__is_active=True,
            is_verified=True,
            user__is_staff=False,
        )
    else:
        friends = user.account.friends

    for friend in friends:
        if friend.user.is_online:
            online_friends.append(friend)
        else:
            offline_friends.append(friend)

    return {
        'requests': list_requests(user),
        'online': online_friends,
        'offline': offline_friends,
    }


def add_friend(from_user: User, username: str):
    try:
        to_user_account = Account.objects.get(username=username)
    except Account.DoesNotExist as e:
        logging.warning(e)
        raise HttpError(400, _('User not found.'))

    friendship, created = models.Friendship.objects.filter(
        Q(user_from=from_user)
        | Q(user_to=from_user)
        | Q(user_from=to_user_account.user)
        | Q(user_to=to_user_account.user),
    ).get_or_create(defaults={'user_from': from_user, 'user_to': to_user_account.user})

    if created:
        websocket.ws_friend_request(friendship)
        notification = to_user_account.notify(
            content=_(f'{from_user.account.username} sent a friend request.'),
            from_user_id=from_user.id,
        )
        ws_new_notification(notification)

    return friendship


def remove_friend(user: User, friend_id: int):
    friend = get_object_or_404(User, pk=friend_id)
    friendship = user.account.get_friendship(friend)
    if friendship:
        friendship.delete()

    websocket.ws_friend_remove(user, friend)
    return {}


def accept_request(user: User, friendship_id: int):
    friendship = get_object_or_404(models.Friendship, pk=friendship_id, user_to=user)
    friendship.accept_date = timezone.now()
    friendship.save()

    websocket.ws_friends_add(friendship.user_to, friendship.user_from)
    return friendship.user_from.account


def refuse_request(user: User, friendship_id: int):
    friendship = get_object_or_404(models.Friendship, pk=friendship_id, user_to=user)
    friendship.delete()
    return {}


def list_requests(user: User):
    sent = models.Friendship.objects.filter(user_from=user, accept_date__isnull=True)
    received = models.Friendship.objects.filter(user_to=user, accept_date__isnull=True)

    return {
        'sent': [schemas.FriendshipSchema.from_orm(friendship) for friendship in sent],
        'received': [
            schemas.FriendshipSchema.from_orm(friendship) for friendship in received
        ],
    }
