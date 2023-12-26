from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from matches.models import Match
from pre_matches.models import Team


class Command(BaseCommand):
    def handle(self, *args, **options):
        teams = Team.get_all()
        Match.objects.filter(
            status=Match.Status.LOADING,
            create_date__lt=timezone.now() - timedelta(seconds=15),
        ).delete()

        for team in teams:
            for lobby in team.lobbies:
                if lobby.players_count < 1 or not lobby.queue:
                    try:
                        team.remove_lobby(lobby.id)
                    except Exception:
                        continue

                    print(f'removing lobby {lobby.id} from team {team.id}')
