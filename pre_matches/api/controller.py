import logging
import time
from typing import Union

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja.errors import Http404, HttpError

from accounts.websocket import ws_update_status_on_friendlist, ws_update_user
from core.websocket import ws_create_toast
from matches.api.controller import cancel_match
from matches.api.schemas import FiveMMatchResponseMock, MatchFiveMSchema
from matches.models import Match, MatchPlayer, Server
from matches.tasks import (
    mock_fivem_match_cancel,
    mock_fivem_match_start,
    send_server_almost_full_mail,
    send_servers_full_mail,
)
from matches.websocket import ws_match_create, ws_match_update

from .. import models, websocket

User = get_user_model()


def get_pre_match_cancel_translated_message(msg_type):
    messages = {
        'lock_in': _('Match cancelled due to user not locked in.'),
        'servers_full': _(
            'All our servers are unavailable at this moment. Please, try again later.'
        ),
        'dodge': _(
            'Some players in your lobby were not ready before the'
            'timer ran out and the match was cancelled. The recurrence'
            'of this conduct may result in restrictions.'
        ),
    }

    return messages.get(msg_type, msg_type)


def cancel_pre_match(
    pre_match: models.PreMatch,
    toast_msg_type: str = None,
    toast_players_id: list = [],
):
    if toast_msg_type:
        translated_msg = get_pre_match_cancel_translated_message(toast_msg_type)
        toast_ids = toast_players_id or [player.id for player in pre_match.players]
        for player_id in toast_ids:
            ws_create_toast(translated_msg, 'warning', user_id=player_id)

    # send ws call to lobbies to cancel that match
    websocket.ws_pre_match_delete(pre_match)
    for player in pre_match.players:
        ws_update_user(player)
        ws_update_status_on_friendlist(player)

    # delete the pre_match and teams from Redis
    team1 = pre_match.teams[0]
    if team1:
        team1.delete()
    team2 = pre_match.teams[1]
    if team2:
        team2.delete()

    models.PreMatch.delete(pre_match.id)


def handle_create_fivem_match(match: Match) -> Match:
    if (
        settings.ENVIRONMENT == settings.LOCAL
        or settings.TEST_MODE
        or settings.FIVEM_MATCH_MOCKS_ON
    ):
        status_code = 201 if settings.FIVEM_MATCH_MOCK_CREATION_SUCCESS else 400
        fivem_response = FiveMMatchResponseMock.from_orm({'status_code': status_code})
        time.sleep(settings.FIVEM_MATCH_MOCK_DELAY_CONFIGURE)
    else:
        server_url = f'http://{match.server.ip}:{match.server.api_port}/api/matches'
        payload = MatchFiveMSchema.from_orm(match).dict()
        try:
            fivem_response = requests.post(
                server_url,
                json=payload,
                timeout=settings.FIVEM_MATCH_CREATION_RETRIES_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            fivem_response = FiveMMatchResponseMock.from_orm({'status_code': 400})
            logging.warning(f'[handle_create_fivem_match] {match.id}')
            return None

    return fivem_response


def handle_create_match_teams(match: Match, pre_match: models.PreMatch) -> Match:
    pre_team1, pre_team2 = pre_match.teams
    if not pre_team1 or not pre_match:
        return

    team_a = match.matchteam_set.create(name=pre_team1.name)
    team_b = match.matchteam_set.create(name=pre_team2.name)

    for user in pre_match.team1_players:
        MatchPlayer.objects.create(user=user, team=team_a)

    for user in pre_match.team2_players:
        MatchPlayer.objects.create(user=user, team=team_b)

    websocket.ws_pre_match_delete(pre_match)
    models.PreMatch.delete(pre_match.id)
    pre_team1.delete()
    pre_team2.delete()

    return (team_a, team_b)


def handle_create_match(pre_match: models.PreMatch) -> Match:
    server = Server.get_idle()
    if not server:
        send_servers_full_mail.delay()
        return

    if (
        len(pre_match.team1_players) < settings.TEAM_READY_PLAYERS_MIN
        or len(pre_match.team2_players) < settings.TEAM_READY_PLAYERS_MIN
        or len(pre_match.team1_players) > pre_match.mode
        or len(pre_match.team2_players) > pre_match.mode
    ):
        cancel_pre_match(pre_match)
        return

    match = Match.objects.create(
        server=server,
        game_type=pre_match.match_type,
        game_mode=pre_match.mode,
    )

    if server.is_almost_full:
        send_server_almost_full_mail.delay(server.name)

    if not handle_create_match_teams(match, pre_match):
        cancel_match(match.id)
        return

    ws_match_create(match)
    for match_player in match.players:
        ws_update_user(match_player.user)
        ws_update_status_on_friendlist(match_player.user)

    return match


def handle_pre_match_checks(user: User, error: str) -> models.PreMatch:
    pre_match = user.account.pre_match
    if not pre_match:
        raise Http404()

    for player in pre_match.players:
        if player.account.get_match() is not None:
            raise HttpError(403, error)

    return pre_match


def get_pre_match(user: User) -> models.PreMatch:
    return user.account.pre_match


def set_player_ready(user: User) -> Union[models.PreMatch, Match]:
    handle_pre_match_checks(
        user,
        _('Can\'t ready in for a new match while in a match.'),
    )

    pre_match = user.account.pre_match
    if user in pre_match.players_ready:
        raise HttpError(400, _('Player already set as ready.'))

    pre_match.set_player_ready(user.id)
    websocket.ws_pre_match_update(pre_match)
    if len(pre_match.players_ready) >= len(pre_match.players):
        match = handle_create_match(pre_match)
        if not match:
            # cancel match due to lack of available servers
            return cancel_pre_match(pre_match, 'servers_full')
        else:
            fivem_response = handle_create_fivem_match(match)
            if fivem_response.status_code != 201:
                cancel_match(match.id)
                return match
            else:
                match.warmup()
                if (
                    settings.ENVIRONMENT == settings.LOCAL
                    or settings.TEST_MODE
                    or settings.FIVEM_MATCH_MOCKS_ON
                ):
                    if settings.FIVEM_MATCH_MOCK_START_SUCCESS:
                        mock_fivem_match_start.apply_async(
                            (match.id,),
                            countdown=settings.FIVEM_MATCH_MOCK_DELAY_START,
                            serializer='json',
                        )
                    else:
                        mock_fivem_match_cancel.apply_async(
                            (match.id,),
                            countdown=settings.FIVEM_MATCH_MOCK_DELAY_START,
                            serializer='json',
                        )

                ws_match_update(match)

            return match

    return pre_match
