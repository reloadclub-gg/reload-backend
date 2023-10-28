from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _

from core.websocket import ws_create_toast, ws_maintenance
from lobbies.models import Lobby
from pre_matches.api.controller import cancel_pre_match
from pre_matches.models import PreMatch, Team

from .models import AppSettings


def handle_start_maintanence():
    # cancel all lobby queues
    Lobby.cancel_all_queues()

    # cancel all pre_matches
    all_pre_matches = PreMatch.get_all()
    for pre_match in all_pre_matches:
        cancel_pre_match(pre_match)

    # delete all teams
    all_teams = Team.get_all()
    for team in all_teams:
        team.delete()

    # send websockets
    message = _(
        'We\'re about to start a maintenance. All queues and invites will be disabled.'
    )
    ws_maintenance('start')
    ws_create_toast(message, variant='warning')


def handle_stop_maintanence():
    # send websockets
    message = _('The maintenance is over. Queues and invites were enabled again. GLHF!')
    ws_maintenance('end')
    ws_create_toast(message, variant='success')


@receiver(post_save, sender=AppSettings)
def update_maintanence(sender, instance: AppSettings, created: bool, **kwargs):
    if not created and instance.name == 'Maintenance Window':
        if AppSettings.get(instance.name) is True:
            handle_start_maintanence()
        else:
            handle_stop_maintanence()
