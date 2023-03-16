import time

from celery import shared_task
from django.contrib.auth import get_user_model

from core.redis import RedisClient
from matchmaking.models import PreMatch, PreMatchConfig
from websocket import controller as ws_controller

cache = RedisClient()
User = get_user_model()


@shared_task
def cancel_match_after_countdown(pre_match_id: str):
    try:
        pre_match = PreMatch.get_by_id(pre_match_id)
    except Exception as exc:
        raise exc

    if pre_match.countdown >= PreMatchConfig.READY_COUNTDOWN_GAP:
        # schedule this task again two seconds later
        time.sleep(2)
        return cancel_match_after_countdown(pre_match.id)

    if pre_match.state != PreMatchConfig.STATES.get('ready'):
        # send ws call to lobbies to cancel that match
        ws_controller.match_cancel(pre_match)
        for user in pre_match.players:
            ws_controller.user_status_change(user)

        # re-start queue for lobbies which all players accepted
        lobbies = pre_match.teams[0].lobbies + pre_match.teams[1].lobbies
        ready_players_ids = [player.id for player in pre_match.players_ready]
        for lobby in lobbies:
            if all(elem in ready_players_ids for elem in lobby.players_ids):
                ws_controller.restart_queue(lobby)
            else:
                ws_controller.match_cancel_warn(lobby)
                # TODO apply some penalty to players with consecutive dodges
                # https://github.com/3C-gg/reload-backend/issues/275

        # delete the pre_match and teams from Redis
        team1 = pre_match.teams[0]
        team2 = pre_match.teams[1]
        team1.delete()
        team2.delete()
        PreMatch.delete(pre_match.id)
