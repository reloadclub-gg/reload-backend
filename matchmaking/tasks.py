import time

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.redis import RedisClient
from matchmaking.models import Player, PreMatch, PreMatchConfig
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
        team1 = pre_match.teams[0]
        team2 = pre_match.teams[1]
        lobbies = team1.lobbies + team2.lobbies
        ready_players_ids = [player.id for player in pre_match.players_ready]
        for lobby in lobbies:
            if all(elem in ready_players_ids for elem in lobby.players_ids):
                ws_controller.restart_queue(lobby)
            else:
                ws_controller.match_cancel_warn(lobby)
                for player_id in lobby.players_ids:
                    if player_id not in ready_players_ids:
                        player = Player.get_by_user_id(player_id)
                        player.dodge_add()

        # delete the pre_match and teams from Redis
        team1.delete()
        team2.delete()
        PreMatch.delete(pre_match.id)


@shared_task
def clear_dodges():
    players = Player.get_all()
    last_week = timezone.now() - timezone.timedelta(weeks=1)
    for player in players:
        if player.latest_dodge and player.latest_dodge <= last_week:
            player.dodge_clear()
