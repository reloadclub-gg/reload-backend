import random

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from ... import models

User = get_user_model()


class Command(BaseCommand):
    help = "Simulate an existing match update from FiveM server"

    def add_arguments(self, parser):
        parser.add_argument(
            'match_id',
            type=int,
            help='The match ID you want to update.',
        )
        parser.add_argument(
            '--finish',
            action='store_true',
            help='Pass this flag if you want to finish the match.',
            default=False,
        )

    def handle(self, *args, **options):
        if settings.ENVIRONMENT == settings.PRODUCTION:
            raise CommandError(
                "This command cannot be run in the production environment."
            )

        try:
            match = models.Match.objects.get(
                pk=options['match_id'],
                status=models.Match.Status.RUNNING,
            )
        except models.Match.DoesNotExist:
            raise CommandError(
                f"No match found with ID {options['match_id']} and status RUNNING."
            )

        url = f'{settings.DOCKER_SITE_URL}/api/matches/{match.id}/'
        response = requests.patch(
            url,
            json={
                'team_a_score': random.randint(0, settings.MATCH_ROUNDS_TO_WIN - 1)
                if not options['finish']
                else settings.MATCH_ROUNDS_TO_WIN,
                'team_b_score': random.randint(0, settings.MATCH_ROUNDS_TO_WIN - 1),
                'end_reason': None,
                'players_stats': [],
                'is_overtime': False,
                'chat': [],
            },
        )

        if response.status_code != 200:
            raise CommandError(
                f"Failed to update the match. Server responded with: {response.status_code}"
            )

        self.stdout.write(self.style.SUCCESS(f"Match {match.id} updated successfully!"))
