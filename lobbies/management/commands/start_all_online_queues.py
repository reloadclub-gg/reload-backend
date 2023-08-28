from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from websocket.utils import ws_send

User = get_user_model()


class Command(BaseCommand):
    help = "Start all queues for all online users."

    def handle(self, *args, **options):
        if settings.ENVIRONMENT == settings.PRODUCTION:
            return

        async_to_sync(ws_send)(
            'lobbies/queue_start',
            None,
            groups=[user.account.lobby.owner_id for user in User.online_users()],
        )
