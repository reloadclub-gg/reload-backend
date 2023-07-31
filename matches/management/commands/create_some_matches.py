import traceback

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

from ... import models

User = get_user_model()


class Command(BaseCommand):
    help = "Create fake matches to test purposes."
    match = None

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "total",
            nargs="+",
            type=int,
            help='The amount of matches to create.',
        )

    def handle(self, *args, **options):
        if settings.ENVIRONMENT == settings.PRODUCTION:
            return

        try:
            server, _ = models.Server.objects.get_or_create(
                ip='123.123.123.123',
                name='Reload 1',
            )

            for i in range(0, options['total'][0]):
                self.match = models.Match.objects.create(
                    server=server,
                    game_type=models.Match.GameType.COMPETITIVE,
                    game_mode=models.Match.GameMode.DEFUSE,
                    status=models.Match.Status.FINISHED,
                    start_date=timezone.now(),
                    end_date=timezone.now(),
                )
                team1 = models.MatchTeam.objects.create(
                    match=self.match,
                    name='Team A',
                    score=settings.MATCH_ROUNDS_TO_WIN,
                )
                models.MatchTeam.objects.create(
                    match=self.match,
                    name='Team B',
                    score=0,
                )
                player = User.objects.filter(
                    is_staff=False,
                    account__is_verified=True,
                ).first()
                models.MatchPlayer.objects.create(team=team1, user=player)

        except Exception as e:
            print(e)
            print(traceback.format_exc())
