from django.contrib.auth import get_user_model

from accounts.models import Account
from core.redis import RedisClient
from steam import Steam

User = get_user_model()
cache = RedisClient()


def fetch_steam_friends(user: User) -> list:
    steam_friends = Steam.get_player_friends(user.steam_user)
    steam_friends_ids = {
        friend['steamid']
        for friend in steam_friends
        if friend['steamid'] != user.steam_user.steamid
    }

    # it will perform better by getting all accounts and then
    # filter the steamids in python
    all_accounts = Account.objects.filter(
        user__is_active=True,
        is_verified=True,
        user__is_staff=False,
    ).prefetch_related('user')

    friends_accounts = [
        account for account in all_accounts if account.steamid in steam_friends_ids
    ]

    if friends_accounts:
        cache.sadd(
            f'__friendlist:user:{user.id}',
            *[friend_account.user.id for friend_account in friends_accounts],
        )

    return friends_accounts


def list(user: User) -> dict:
    friends = fetch_steam_friends(user)

    # create empty lists for online and offline friends
    online_friends, offline_friends = [], []

    # Loop through friends once and add them to the respective lists
    for friend in friends:
        if friend.user.is_online:
            online_friends.append(friend)
        else:
            offline_friends.append(friend)

    return {
        'online': online_friends,
        'offline': offline_friends,
    }
