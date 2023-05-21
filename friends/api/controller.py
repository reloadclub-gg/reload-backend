from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja.errors import HttpError

from accounts.models import Account

User = get_user_model()


def list(user: User):
    return {
        'online': user.account.online_friends,
        'offline': [
            friend for friend in user.account.friends if not friend.user.is_online
        ],
    }


def detail(user: User, friend_id: int):
    friend = get_object_or_404(
        Account, user__id=friend_id, is_verified=True, user__is_active=True
    )
    if not user.account.check_friendship(friend):
        raise HttpError(400, _('Users aren\'t friends.'))

    return friend
