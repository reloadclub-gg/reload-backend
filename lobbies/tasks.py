from celery import shared_task
from django.utils import timezone

from lobbies.models import Player


@shared_task
def clear_dodges():
    players = Player.get_all()
    last_week = timezone.now() - timezone.timedelta(weeks=1)
    for player in players:
        if player.latest_dodge and player.latest_dodge <= last_week:
            player.dodge_clear()
