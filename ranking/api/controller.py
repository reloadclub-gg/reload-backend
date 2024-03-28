from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import Account

from . import schemas

User = get_user_model()


def ranking_list() -> dict:
    accounts = (
        Account.verified_objects.all()
        .only("level", "level_points", "username", "user")
        .order_by("-level", "-level_points")[: settings.RANKING_LIMIT]
    )
    return [
        schemas.RankingItemSchema(
            id=account.id,
            level=account.level,
            level_points=account.level_points,
            username=account.username,
            user=account.user,
            avatar=account.avatar_dict,
            ranking_pos=index + 1,
            user_id=account.user.id,
            steam_url=account.user.steam_user.profileurl,
            matches_played=account.get_matches_played_count(),
            matches_won=account.matches_won,
        )
        for index, account in enumerate(accounts)
    ]
