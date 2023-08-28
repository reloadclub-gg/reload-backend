import time
from typing import List

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils.translation import activate
from django.utils.translation import gettext as _

from accounts.websocket import ws_update_user
from core.websocket import ws_create_toast
from friends.websocket import ws_friend_update_or_create
from lobbies.models import Lobby, Player
from lobbies.tasks import end_player_restriction
from lobbies.websocket import ws_queue_start, ws_update_lobby

from . import models, websocket

User = get_user_model()


def get_match(pre_match_id: int) -> models.PreMatch:
    try:
        return models.PreMatch.get_by_id(pre_match_id)
    except models.PreMatchException:
        # we have deleted the pre_match already in favor of a match
        return None


def handle_cancel_match_ws(pre_match: models.PreMatch):
    websocket.ws_pre_match_delete(pre_match)
    for player in pre_match.players:
        ws_update_user(player)
        ws_friend_update_or_create(player)


def handle_delete_from_cache(team1: models.Team, team2: models.Team, pre_match_id: int):
    models.PreMatch.delete(pre_match_id)
    team1.delete()
    team2.delete()


def handle_dodges(lobby: Lobby, ready_players_ids: List[int]):
    for player_id in lobby.players_ids:
        msg = _(
            'Some players in your lobby were not ready before the'
            'timer ran out and the match was cancelled. The recurrence'
            'of this conduct may result in restrictions.'
        )
        ws_create_toast(player_id, msg, 'warning')
        if player_id not in ready_players_ids:
            player = Player.get_by_user_id(player_id)
            restriction_end_date = player.dodge_add()
            if restriction_end_date:
                end_player_restriction.apply_async(
                    (player_id,),
                    eta=restriction_end_date,
                    serializer='json',
                )


@shared_task
def cancel_match_after_countdown(pre_match_id: int, lang: str = None):
    pre_match = get_match(pre_match_id)
    if not pre_match:
        return

    lang and activate(lang)

    if pre_match.countdown >= models.PreMatch.Config.READY_COUNTDOWN_GAP:
        # schedule this task again two seconds later
        time.sleep(2)
        return cancel_match_after_countdown(pre_match.id)

    if pre_match.state != models.PreMatch.Config.STATES.get('ready'):
        team1 = pre_match.teams[0]
        team2 = pre_match.teams[1]
        lobbies = team1.lobbies + team2.lobbies

        # send ws call to lobbies to cancel that match
        handle_cancel_match_ws(pre_match)

        # get ready_players_ids before we delete pre_match keys from Redis
        ready_players_ids = [player.id for player in pre_match.players_ready]

        # delete the pre_match and teams from Redis
        handle_delete_from_cache(team1, team2, pre_match_id)

        # re-start queue for lobbies which all players accepted
        for lobby in lobbies:
            if all(elem in ready_players_ids for elem in lobby.players_ids):
                ws_queue_start(lobby)
            else:
                handle_dodges(lobby, ready_players_ids)

            ws_update_lobby(lobby)
