from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja.errors import AuthenticationError, Http404, HttpError

from matches.models import Match, MatchPlayer
from websocket import controller as ws_controller

from ..models import (
    Lobby,
    LobbyException,
    LobbyInvite,
    LobbyInviteException,
    PreMatch,
    PreMatchConfig,
    PreMatchException,
    Team,
)
from ..tasks import cancel_match_after_countdown

User = get_user_model()


def lobby_remove_player(lobby_id: int, user_id: int) -> Lobby:
    current_lobby = Lobby(owner_id=lobby_id)
    user_lobby = Lobby(owner_id=user_id)

    Lobby.move(user_id, to_lobby_id=user_id)

    current_lobby_players = [
        User.objects.get(pk=player_id) for player_id in current_lobby.players_ids
    ]
    for player in current_lobby_players:
        ws_controller.user_status_change(player)
        ws_controller.user_update(player)

    ws_controller.lobby_update([current_lobby, user_lobby])

    user = User.objects.get(pk=user_id)
    ws_controller.user_status_change(user)
    ws_controller.user_update(user)

    return current_lobby


def lobby_invite(lobby_id: int, from_user_id: int, to_user_id: int) -> LobbyInvite:
    lobby = Lobby(owner_id=lobby_id)

    try:
        invite = lobby.invite(from_user_id, to_user_id)
        ws_controller.lobby_player_invite(invite)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return invite


def lobby_refuse_invite(lobby_id: int, invite_id: str):
    lobby = Lobby(owner_id=lobby_id)

    try:
        invite = LobbyInvite.get(lobby_id, invite_id)
        ws_controller.lobby_player_refuse_invite(invite)
        lobby.delete_invite(invite_id)
    except (LobbyException, LobbyInviteException) as exc:
        raise HttpError(400, str(exc))

    return invite


def lobby_change_type_and_mode(
    lobby_id: int, lobby_type: str, lobby_mode: int
) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    try:
        lobby.set_type(lobby_type)
        lobby.set_mode(lobby_mode)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    ws_controller.lobby_update([lobby])

    return lobby


def lobby_enter(user: User, lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    try:
        Lobby.move(user.id, lobby_id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    ws_controller.lobby_update([lobby])
    ws_controller.user_status_change(user)
    ws_controller.lobby_invites_update(lobby)

    lobby_players = [User.objects.get(pk=player_id) for player_id in lobby.players_ids]
    for player in lobby_players:
        ws_controller.user_status_change(player)
        ws_controller.user_update(player)

    return lobby


def set_public(lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)
    lobby.set_public()
    ws_controller.lobby_update([lobby])

    return lobby


def set_private(lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)
    lobby.set_private()
    ws_controller.lobby_update([lobby])

    return lobby


def lobby_accept_invite(user: User, lobby_id: int, invite_id: str) -> Lobby:
    current_lobby = user.account.lobby
    new_lobby = Lobby(owner_id=lobby_id)

    if current_lobby.id == new_lobby.id:
        raise HttpError(400, _('Can\'t accept an invite from the same lobby.'))

    try:
        LobbyInvite.get(lobby_id=lobby_id, invite_id=invite_id)
    except LobbyInviteException as exc:
        raise HttpError(400, str(exc))

    if user.id in new_lobby.players_ids:
        new_lobby.delete_invite(invite_id)
        return new_lobby

    lobby_leave(user)
    lobby_enter(user, new_lobby.id)
    return new_lobby


def lobby_leave(user: User) -> User:
    current_lobby = user.account.lobby
    user_lobby = Lobby(owner_id=user.id)
    lobbies_update = [current_lobby, user_lobby]
    try:
        new_lobby = Lobby.move(user.id, to_lobby_id=user.id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    if new_lobby:
        lobbies_update.append(new_lobby)
        for user_id in new_lobby.players_ids:
            ws_controller.user_status_change(User.objects.get(pk=user_id))
            ws_controller.user_update(User.objects.get(pk=user_id))

    current_lobby_players = [
        User.objects.get(pk=player_id) for player_id in current_lobby.players_ids
    ]
    for player in current_lobby_players:
        ws_controller.user_status_change(player)
        ws_controller.user_update(player)
    ws_controller.lobby_update(lobbies_update)
    ws_controller.user_status_change(user)

    return user


def lobby_start_queue(lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)

    try:
        lobby.start_queue()
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    ws_controller.lobby_update([lobby])
    ws_controller.lobby_invites_update(lobby, expired=True)
    for invite in lobby.invites:
        lobby.delete_invite(invite.id)
    for user_id in lobby.players_ids:
        ws_controller.user_status_change(User.objects.get(pk=user_id))

    team = Team.find(lobby) or Team.build(lobby)
    if team and team.ready:
        opponent = team.get_opponent_team()
        if opponent:
            lobbies = team.lobbies + opponent.lobbies
            for lobby in lobbies:
                lobby.cancel_queue()
                ws_controller.lobby_update(lobbies)

            pre_match = PreMatch.create(team.id, opponent.id)
            ws_controller.pre_match(pre_match)
            for user in pre_match.players:
                ws_controller.user_status_change(user)

    return lobby


def lobby_cancel_queue(lobby_id: int):
    lobby = Lobby(owner_id=lobby_id)
    lobby.cancel_queue()

    ws_controller.lobby_update([lobby])
    for user_id in lobby.players_ids:
        ws_controller.user_status_change(User.objects.get(pk=user_id))

    team = Team.get_by_lobby_id(lobby_id, fail_silently=True)
    if team:
        team.remove_lobby(lobby_id)

    return lobby


def match_player_lock_in(user: User, pre_match_id: str):
    try:
        pre_match = PreMatch.get_by_id(pre_match_id)
    except PreMatchException:
        raise Http404()

    if user not in pre_match.players:
        raise AuthenticationError()

    pre_match.set_player_lock_in()
    if pre_match.players_in >= PreMatchConfig.READY_PLAYERS_MIN:
        pre_match.start_players_ready_countdown()
        ws_controller.pre_match(pre_match)
        # delay task to check if countdown is over to READY_COUNTDOWN seconds
        # plus READY_COUNTDOWN_GAP (that should be turned into a positive number)
        cancel_match_after_countdown.apply_async(
            (pre_match.id,),
            countdown=PreMatchConfig.READY_COUNTDOWN
            + (-PreMatchConfig.READY_COUNTDOWN_GAP),
            serializer='json',
        )

    return pre_match


def match_player_ready(user: User, pre_match_id: str):
    try:
        pre_match = PreMatch.get_by_id(pre_match_id)
    except PreMatchException:
        raise Http404()

    if user not in pre_match.players:
        raise AuthenticationError()

    if user in pre_match.players_ready:
        raise HttpError(400, _('Player already set as ready.'))

    pre_match.set_player_ready(user.id)
    ws_controller.pre_match(pre_match)
    if len(pre_match.players_ready) >= PreMatchConfig.READY_PLAYERS_MIN:
        create_match(pre_match)

    return pre_match


def create_match(pre_match) -> Match:
    game_type, game_mode = pre_match.teams[0].type_mode
    match = Match.objects.create(game_type=game_type, game_mode=game_mode)

    for user in pre_match.team1_players:
        MatchPlayer.objects.create(user=user, match=match, team=Match.Teams.TEAM_A)

    for user in pre_match.team2_players:
        MatchPlayer.objects.create(user=user, match=match, team=Match.Teams.TEAM_B)

    # TODO start match on the FiveM server
    # (https://github.com/3C-gg/reload-backend/issues/243)

    return match
