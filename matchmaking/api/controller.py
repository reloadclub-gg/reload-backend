from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja.errors import AuthenticationError, Http404, HttpError

from matches.models import Match, MatchPlayer, Server
from websocket.tasks import match_task, pre_match_task, user_status_change_task

from ..models import PreMatch, PreMatchConfig, PreMatchException
from ..tasks import cancel_match_after_countdown

User = get_user_model()


def match_player_lock_in(user: User, pre_match_id: str) -> PreMatch:
    if user.account.match:
        raise HttpError(403, _('Can\'t lock in for a new match while in a match.'))

    try:
        pre_match = PreMatch.get_by_id(pre_match_id)
    except PreMatchException:
        raise Http404()

    if user not in pre_match.players:
        raise AuthenticationError()

    pre_match.set_player_lock_in()
    if pre_match.players_in >= PreMatchConfig.READY_PLAYERS_MIN:
        pre_match.start_players_ready_countdown()
        pre_match_task.delay(pre_match.id)
        # delay task to check if countdown is over to READY_COUNTDOWN seconds
        # plus READY_COUNTDOWN_GAP (that should be turned into a positive number)
        cancel_match_after_countdown.apply_async(
            (pre_match.id,),
            countdown=PreMatchConfig.READY_COUNTDOWN
            + (-PreMatchConfig.READY_COUNTDOWN_GAP),
            serializer='json',
        )

    return pre_match


def match_player_ready(user: User, pre_match_id: str) -> PreMatch:
    if user.account.match:
        raise HttpError(403, _('Can\'t ready in for a new match while in a match.'))

    try:
        pre_match = PreMatch.get_by_id(pre_match_id)
    except PreMatchException:
        raise Http404()

    if user not in pre_match.players:
        raise AuthenticationError()

    if user in pre_match.players_ready:
        raise HttpError(400, _('Player already set as ready.'))

    pre_match.set_player_ready(user.id)
    pre_match_task.delay(pre_match.id)
    if len(pre_match.players_ready) >= PreMatchConfig.READY_PLAYERS_MIN:
        create_match(pre_match)

    return pre_match


def create_match(pre_match) -> Match:
    server = Server.get_idle()
    if not server:
        # TODO send alert (email, etc) to admins
        # TODO send alert to client app
        return

    game_type, game_mode = pre_match.teams[0].type_mode
    match = Match.objects.create(
        server=server, game_type=game_type, game_mode=game_mode
    )

    pre_team1, pre_team2 = pre_match.teams
    team1 = match.matchteam_set.create(name=pre_team1.name)
    team2 = match.matchteam_set.create(name=pre_team2.name)

    for user in pre_match.team1_players:
        MatchPlayer.objects.create(user=user, team=team1)

    for user in pre_match.team2_players:
        MatchPlayer.objects.create(user=user, team=team2)

    # TODO start match on the FiveM server
    # (https://github.com/3C-gg/reload-backend/issues/243)

    match_task.delay(match.id)
    for match_player in match.players:
        user_status_change_task.delay(match_player.user.id)

    if server.is_almost_full:
        # TODO send alert (email, etc) to admins
        pass

    return match
