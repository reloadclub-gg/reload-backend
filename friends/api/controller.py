from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja.errors import HttpError

from accounts.models import Account
from core.redis import RedisClient
from steam import Steam

User = get_user_model()
cache = RedisClient()


def fetch_steam_friends(user: User) -> list:
    steam_friends = Steam.get_player_friends(user.steam_user)
    steam_friends_ids = [friend.get('steamid') for friend in steam_friends]
    friends_accounts = [
        account
        for account in Account.objects.filter(
            user__is_active=True,
            is_verified=True,
            user__is_staff=False,
            steamid__in=steam_friends_ids,
        ).exclude(user_id=user.id)
    ]

    cache.sadd(
        f'__friendlist:user:{user.id}',
        *[friend_account.user.id for friend_account in friends_accounts],
    )
    return friends_accounts


def list(user: User) -> dict:
    friends = fetch_steam_friends(user)
    return {
        'online': [friend for friend in friends if friend.user.is_online],
        'offline': [friend for friend in friends if not friend.user.is_online],
    }


def detail(user: User, friend_id: int):
    friend = get_object_or_404(
        Account, user__id=friend_id, is_verified=True, user__is_active=True
    )
    if not user.account.check_friendship(friend):
        raise HttpError(400, _('Users aren\'t friends.'))

    return friend
