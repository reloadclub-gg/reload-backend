from django.contrib.auth import get_user_model

from core.redis import RedisClient

User = get_user_model()
cache = RedisClient()


def list(user: User) -> dict:
    friends = user.account.fetch_steam_friends()

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
