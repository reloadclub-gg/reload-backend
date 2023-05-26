from typing import List

from django.contrib.auth import get_user_model

from matches.models import Match, MatchPlayer

User = get_user_model()


def get_user_matches(user: User, user_id: int = None) -> List[Match]:
    search_id = user.id if not user_id else user_id

    matches_ids = MatchPlayer.objects.filter(
        user=search_id,
        team__match__status=Match.Status.FINISHED,
    ).values_list('team__match', flat=True)
    return [Match.objects.get(pk=id) for id in matches_ids]
