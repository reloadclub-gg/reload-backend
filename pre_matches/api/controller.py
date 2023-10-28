import time
from typing import Union

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from ninja.errors import Http404, HttpError

from accounts.websocket import ws_update_user
from core.websocket import ws_create_toast
from friends.websocket import ws_friend_update_or_create
from matches.api.controller import cancel_match
from matches.api.schemas import FiveMMatchResponseMock, MatchFiveMSchema
from matches.models import Match, MatchPlayer, Server
from matches.tasks import mock_fivem_match_cancel, mock_fivem_match_start
from matches.websocket import ws_match_create, ws_match_update

from .. import models, tasks, websocket

User = get_user_model()


def cancel_pre_match(pre_match: models.PreMatch, toast_msg: str = None):
    if toast_msg:
        for player in pre_match.players:
            ws_create_toast(toast_msg, 'warning', user_id=player.id)

    # send ws call to lobbies to cancel that match
    websocket.ws_pre_match_delete(pre_match)
    for player in pre_match.players:
        ws_update_user(player)
        ws_friend_update_or_create(player)

    # delete the pre_match and teams from Redis
    team1 = pre_match.teams[0]
    team2 = pre_match.teams[1]
    models.PreMatch.delete(pre_match.id)
    team1.delete()
    team2.delete()


def handle_create_fivem_match(match: Match) -> Match:
    if settings.ENVIRONMENT == settings.LOCAL or settings.TEST_MODE:
        status_code = 201 if settings.FIVEM_MATCH_MOCK_CREATION_SUCCESS else 400
        fivem_response = FiveMMatchResponseMock.from_orm({'status_code': status_code})
        time.sleep(settings.FIVEM_MATCH_MOCK_DELAY_CONFIGURE)
    else:
        server_url = f'http://{match.server.ip}:{match.server.api_port}/api/matches'
        payload = MatchFiveMSchema.from_orm(match).dict()
        fivem_response = requests.post(server_url, json=payload)

    return fivem_response


def handle_create_match_teams(match: Match, pre_match: models.PreMatch) -> Match:
    pre_team1, pre_team2 = pre_match.teams
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


def handle_create_match(pre_match: models.PreMatch) -> Match:
    server = Server.get_idle()
    if not server:
        # TODO send alert (email, etc) to admins
        return

    game_type, game_mode = pre_match.teams[0].type_mode
    match = Match.objects.create(
        server=server,
        game_type=game_type,
        game_mode=game_mode,
    )

    handle_create_match_teams(match, pre_match)

    ws_match_create(match)
    for match_player in match.players:
        ws_update_user(match_player.user)
        ws_friend_update_or_create(match_player.user)

    if server.is_almost_full:
        # TODO send alert (email, etc) to admins
        pass

    return match


def handle_pre_match_checks(user: User, error: str) -> User:
    if user.account.get_match():
        raise HttpError(403, error)

    if not user.account.pre_match:
        raise Http404()

    return user


def get_pre_match(user: User) -> models.PreMatch:
    return user.account.pre_match


def set_player_lock_in(user: User) -> models.PreMatch:
    handle_pre_match_checks(user, _('Can\'t lock in for a new match while in a match.'))
    pre_match = user.account.pre_match

    if user.id in [player.id for player in pre_match.players_in]:
        raise HttpError(400, _('Player already locked in.'))

    try:
        pre_match.set_player_lock_in(user.id)
    except models.PreMatchException as e:
        raise HttpError(403, e)

    if len(pre_match.players_in) >= len(pre_match.players):
        websocket.ws_pre_match_update(pre_match)
        # delay task to check if countdown is over to READY_COUNTDOWN seconds
        # plus READY_COUNTDOWN_GAP (that should be turned into a positive number)
        lang = get_language()
        tasks.cancel_match_after_countdown.apply_async(
            (pre_match.id, lang),
            countdown=models.PreMatch.Config.READY_COUNTDOWN
            + (-models.PreMatch.Config.READY_COUNTDOWN_GAP),
            serializer='json',
        )

    return pre_match


def set_player_ready(user: User) -> Union[models.PreMatch, Match]:
    handle_pre_match_checks(
        user,
        _('Can\'t ready in for a new match while in a match.'),
    )

    pre_match = user.account.pre_match
    if user in pre_match.players_ready:
        raise HttpError(400, _('Player already set as ready.'))

    try:
        pre_match.set_player_ready(user.id)
    except models.PreMatchException as e:
        raise HttpError(403, e)

    websocket.ws_pre_match_update(pre_match)
    if len(pre_match.players_ready) >= len(pre_match.players):
        match = handle_create_match(pre_match)
        if not match:
            # cancel match due to lack of available servers
            return cancel_pre_match(
                pre_match,
                _(
                    'All our servers are unavailable at this moment. Please, try again later.'
                ),
            )
        else:
            fivem_response = handle_create_fivem_match(match)
            if fivem_response.status_code != 201:
                cancel_match(match.id)
                return match
            else:
                match.warmup()
                if settings.ENVIRONMENT == settings.LOCAL or settings.TEST_MODE:
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
