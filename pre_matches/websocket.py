from asgiref.sync import async_to_sync

from websocket.utils import ws_send

from . import models
from .api import schemas


def ws_pre_match_create(pre_match: models.PreMatch):
    """
    Notify clients from a Lobby that a match was found. This isn't a Match,
    it is just a verification that all users are ready to play a Match.

    Cases:
    - A match was found for two or more lobbies that became teams filled with players.

    Payload:
    pre_matches.api.schemas.PreMatchSchema: object

    Actions:
    - pre_matches/create
    """
    payload = schemas.PreMatchSchema.from_orm(pre_match).dict()

    return async_to_sync(ws_send)(
        'pre_matches/create',
        payload,
        groups=[player.id for player in pre_match.players],
    )


def ws_pre_match_update(pre_match: models.PreMatch):
    """
    Notify clients from a Lobby that a match was found. This isn't a Match,
    it is just a verification that all users are ready to play a Match.

    Cases:
    - A match was found for two or more lobbies that became teams filled with players.

    Payload:
    pre_matches.api.schemas.PreMatchSchema: object

    Actions:
    - pre_matches/update
    """

    payload = schemas.PreMatchSchema.from_orm(pre_match).dict()
    results = list()

    for player in pre_match.players:
        payload['user_ready'] = player in pre_match.players_ready
        results.append(
            async_to_sync(ws_send)('pre_matches/update', payload, groups=[player.id])
        )
    return results


def ws_pre_match_delete(pre_match: models.PreMatch):
    """
    Triggered when some player didn't get ready by the ready countdown end.
    The match creation is canceled and the pre_match is deleted.
    Lobbies that all players marked theyselves as ready, will get back to queue automatically.
    The ones that have players who didn't get ready in time, will receive a dodge
    in their accounts and can be restricted.

    Cases:
    - Some player didn't marked itself as ready.

    Payload:
    null

    Actions:
    - pre_matches/delete
    """

    groups = [player.id for player in pre_match.players]
    async_to_sync(ws_send)('pre_matches/delete', None, groups=groups)
