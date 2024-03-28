from typing import Dict, List

from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import Account
from matches.models import Match

User = get_user_model()


def ranking_list() -> List[Dict]:
    ranking_list = []

    accounts = (
        Account.verified_objects.all()
        .only("level", "level_points", "username", "user")
        .order_by("-level", "-level_points")[: settings.RANKING_LIMIT]
    )

    finished_matches = Match.objects.filter(status=Match.Status.FINISHED).values_list(
        "id", flat=True
    )

    for idx, account in enumerate(accounts):
        matches = account.user.matchplayer_set.filter(
            team__match__id__in=finished_matches
        )
        ranking_list.append(
            {
                "level": account.level,
                "level_points": account.level_points,
                "username": account.username,
                "user_id": account.user.id,
                "avatar": account.avatar_dict,
                "ranking_pos": idx + 1,
                "steam_url": account.user.steam_user.profileurl,
                "matches_played": matches.count(),
                "matches_won": matches.filter(
                    team__score=settings.MATCH_ROUNDS_TO_WIN,
                ).count(),
            }
        )

    return ranking_list
