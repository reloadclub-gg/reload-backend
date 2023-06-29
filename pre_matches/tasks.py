import time

from celery import shared_task
from django.utils.translation import gettext as _

from accounts.websocket import ws_update_user
from core.websocket import ws_create_toast
from friends.websocket import ws_friend_update_or_create
from lobbies.models import Player
from lobbies.websocket import ws_update_lobby

from . import models, websocket


@shared_task
def cancel_match_after_countdown(pre_match_id: str):
    try:
        pre_match = models.PreMatch.get_by_id(pre_match_id)
    except Exception as exc:
        raise exc

    if pre_match.countdown >= models.PreMatch.Config.READY_COUNTDOWN_GAP:
        # schedule this task again two seconds later
        time.sleep(2)
        return cancel_match_after_countdown(pre_match.id)

    if pre_match.state != models.PreMatch.Config.STATES.get('ready'):
        team1 = pre_match.teams[0]
        team2 = pre_match.teams[1]
        lobbies = team1.lobbies + team2.lobbies

        # re-start queue for lobbies which all players accepted
        ready_players_ids = [player.id for player in pre_match.players_ready]
        for lobby in lobbies:
            if all(elem in ready_players_ids for elem in lobby.players_ids):
                lobby.start_queue()
                ws_update_lobby(lobby)

            else:
                for player_id in lobby.players_ids:
                    msg = _(
                        'Some players in your lobby were not ready'
                        ' before the timer ran out and the match was cancelled.'
                        ' The recurrence of this conduct may result in restrictions.'
                    )
                    ws_create_toast(player_id, msg, 'warning')
                    if player_id not in ready_players_ids:
                        player = Player.get_by_user_id(player_id)
                        player.dodge_add()

        # send ws call to lobbies to cancel that match
        websocket.ws_pre_match_delete(pre_match)
        for player in pre_match.players:
            ws_update_user(player)
            ws_friend_update_or_create(player)

        # delete the pre_match and teams from Redis
        team1.delete()
        team2.delete()
        models.PreMatch.delete(pre_match.id)
