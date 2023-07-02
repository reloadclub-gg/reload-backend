from asgiref.sync import async_to_sync

from websocket.utils import ws_send

from . import models
from .api import schemas


def ws_match_create(match: models.Match):
    """
    A real match is about to start. Notify match players so they can update
    some stuff on FE.

    Cases:
    - All players are ready to start a match.

    Payload:
    matches.api.schemas.MatchSchema: object

    Actions:
    - matches/create/
    """
    payload = schemas.MatchSchema.from_orm(match).dict()

    return async_to_sync(ws_send)(
        'matches/create',
        payload,
        groups=[player.user.id for player in match.players],
    )
