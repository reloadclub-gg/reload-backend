from django.core.management.base import BaseCommand

from accounts.models import Account
from accounts.utils import send_verify_account_mail


class Command(BaseCommand):
    help = "Send an email with verification token for all unverified users."

    def handle(self, *args, **options):
        qs = Account.objects.filter(is_verified=False).values(
            'user__email', 'username', 'verification_token'
        )

        for record in qs:
            print(
                record['user__email'],
                record['username'],
                record['verification_token'],
            )
            send_verify_account_mail(
                record['user__email'],
                record['username'],
                record['verification_token'],
            )
