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
    - matches/create
    """
    payload = schemas.MatchSchema.from_orm(match).dict()

    return async_to_sync(ws_send)(
        'matches/create',
        payload,
        groups=[player.user.id for player in match.players],
    )


def ws_match_update(match: models.Match):
    """
    Update match so client knows what is going on.

    Cases:
    - Match change its state (e.g. from LOADING to RUNNING).
    - Match receive updates from FiveM Server (e.g. round finish).

    Payload:
    matches.api.schemas.MatchSchema: object

    Actions:
    - matches/update
    """
    payload = schemas.MatchSchema.from_orm(match).dict()

    return async_to_sync(ws_send)(
        'matches/update',
        payload,
        groups=[player.user.id for player in match.players],
    )


def ws_match_delete(match: models.Match):
    """
    Delete match for its users on FE.

    Cases:
    - Match was canceled due to external reasons.

    Payload:
    null

    Actions:
    - matches/delete
    """

    return async_to_sync(ws_send)(
        'matches/delete',
        None,
        groups=[player.user.id for player in match.players],
    )
