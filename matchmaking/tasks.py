import time

from celery import shared_task
from django.contrib.auth import get_user_model

from core.redis import RedisClient
from matchmaking.models import PreMatch, PreMatchConfig
from websocket.controller import match_cancel

cache = RedisClient()
User = get_user_model()


@shared_task
def cancel_match_after_countdown(pre_match_id: str):
    try:
        match = PreMatch.get_by_id(pre_match_id)
    except Exception as exc:
        raise exc

    if match.countdown >= PreMatchConfig.READY_COUNTDOWN_GAP:
        # schedule this task again two seconds later
        time.sleep(2)
        return cancel_match_after_countdown(match.id)

    if match.state != PreMatchConfig.STATES.get('ready'):
        # send ws call to lobbies to cancel that match
        lobbies = match.teams[0].lobbies + match.teams[1].lobbies
        match_cancel(lobbies)

        # delete the pre_match from Redis
        PreMatch.delete(match.id)
