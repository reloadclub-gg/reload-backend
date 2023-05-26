from typing import List

from django.contrib.auth import get_user_model

from matches.models import Match, MatchPlayer

User = get_user_model()


def get_user_matches(user: User) -> List[Match]:
    matches_ids = MatchPlayer.objects.filter(
        user=user,
        team__match__status=Match.Status.FINISHED,
    ).values_list('team__match', flat=True)
    return [Match.objects.get(pk=id) for id in matches_ids]
