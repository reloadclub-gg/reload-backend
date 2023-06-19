from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model

from websocket.utils import ws_send

from . import models
from .api import schemas

User = get_user_model()


def ws_match_found(pre_match: models.PreMatch):
    """
    Notify clients from a Lobby that a match was found. This isn't a Match,
    it is just a verification that all users are ready to play a Match.

    Cases:
    - A match was found for two or more lobbies that became teams filled with players.

    Payload:
    matchmaking.api.schemas.PreMatchSchema: object

    Actions:
    - matches/found
    """
    payload = schemas.PreMatchSchema.from_orm(pre_match).dict()

    return async_to_sync(ws_send)(
        'matches/found',
        payload,
        groups=[player.id for player in pre_match.players],
    )
