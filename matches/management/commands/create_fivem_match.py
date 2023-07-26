import traceback

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser
from django.test import override_settings
from model_bakery import baker

from accounts.models import Account
from accounts.utils import create_social_auth
from pre_matches.api.controller import handle_create_fivem_match

from ... import models

User = get_user_model()


class Command(BaseCommand):
    help = "Create a match and send it to FiveM."
    match = None

    def add_arguments(self, parser: CommandParser) -> None:
        super().add_arguments(parser)
        parser.add_argument(
            "server_ip",
            nargs="+",
            type=str,
            help='Ther server IP which the script should make requests.',
        )

    def prepare(self):
        self.users = []
        User.objects.filter(email__contains='user_test_create_fivem_match').delete()

        self.user_1 = baker.make(
            User,
            email='user_test_create_fivem_match_1@example.com',
            is_active=True,
        )
        create_social_auth(self.user_1)
        baker.make(Account, user=self.user_1, is_verified=True)
        self.users.append(self.user_1)

        self.user_2 = baker.make(
            User,
            email='user_test_create_fivem_match_2@example.com',
            is_active=True,
        )
        create_social_auth(self.user_2)
        baker.make(Account, user=self.user_2, is_verified=True)
        self.users.append(self.user_2)

        self.user_3 = baker.make(
            User,
            email='user_test_create_fivem_match_3@example.com',
            is_active=True,
        )
        create_social_auth(self.user_3)
        baker.make(Account, user=self.user_3, is_verified=True)
        self.users.append(self.user_3)

        self.user_4 = baker.make(
            User,
            email='user_test_create_fivem_match_4@example.com',
            is_active=True,
        )
        create_social_auth(self.user_4)
        baker.make(Account, user=self.user_4, is_verified=True)
        self.users.append(self.user_4)

        self.user_5 = baker.make(
            User,
            email='user_test_create_fivem_match_5@example.com',
            is_active=True,
        )
        create_social_auth(self.user_5)
        baker.make(Account, user=self.user_5, is_verified=True)
        self.users.append(self.user_5)

        self.user_6 = baker.make(
            User,
            email='user_test_create_fivem_match_6@example.com',
            is_active=True,
        )
        create_social_auth(self.user_6)
        baker.make(Account, user=self.user_6, is_verified=True)
        self.users.append(self.user_6)

        self.user_7 = baker.make(
            User,
            email='user_test_create_fivem_match_7@example.com',
            is_active=True,
        )
        create_social_auth(self.user_7)
        baker.make(Account, user=self.user_7, is_verified=True)
        self.users.append(self.user_7)

        self.user_8 = baker.make(
            User,
            email='user_test_create_fivem_match_8@example.com',
            is_active=True,
        )
        create_social_auth(self.user_8)
        baker.make(Account, user=self.user_8, is_verified=True)
        self.users.append(self.user_8)

        self.user_9 = baker.make(
            User,
            email='user_test_create_fivem_match_9@example.com',
            is_active=True,
        )
        create_social_auth(self.user_9)
        baker.make(Account, user=self.user_9, is_verified=True)
        self.users.append(self.user_9)

        self.user_10 = baker.make(
            User, email='user_test_create_fivem_match_10@example.com', is_active=True
        )
        create_social_auth(self.user_10)
        baker.make(Account, user=self.user_10, is_verified=True)
        self.users.append(self.user_10)

        self.team1_users = [
            self.user_1,
            self.user_2,
            self.user_3,
            self.user_4,
            self.user_5,
        ]

        self.team2_users = [
            self.user_6,
            self.user_7,
            self.user_8,
            self.user_9,
            self.user_10,
        ]

    def tear_down(self):
        if self.match:
            self.match.delete()

        for user in self.users:
            user.delete()

        assert (
            len(User.objects.filter(email__contains='user_test_create_fivem_match'))
            == 0
        )

    @override_settings(ENVIRONMENT=settings.STAGING)
    def fivem_request(self):
        return handle_create_fivem_match(self.match)

    def handle(self, *args, **options):
        if settings.ENVIRONMENT == settings.PRODUCTION:
            return

        self.prepare()

        try:
            server, _ = models.Server.objects.get_or_create(
                ip=options['server_ip'][0],
                name='Reload Staging Server',
            )

            self.match = models.Match.objects.create(
                server=server,
                game_type=models.Match.GameType.COMPETITIVE,
                game_mode=models.Match.GameMode.DEFUSE,
            )
            team1 = models.MatchTeam.objects.create(match=self.match, name='team1')
            team2 = models.MatchTeam.objects.create(match=self.match, name='team2')

            [
                models.MatchPlayer.objects.create(user=user, team=team1)
                for user in self.team1_users
            ]
            [
                models.MatchPlayer.objects.create(user=user, team=team2)
                for user in self.team2_users
            ]

            response = self.fivem_request()
            print(response)

        except Exception as e:
            print(e)
            print(traceback.format_exc())

        self.tear_down()
