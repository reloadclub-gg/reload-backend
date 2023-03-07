from django.contrib.auth import get_user_model
from ninja.errors import AuthenticationError, Http404, HttpError

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

User = get_user_model()


def lobby_remove_player(lobby_id: int, user_id: int) -> Lobby:
    current_lobby = Lobby(owner_id=lobby_id)
    user_lobby = Lobby(owner_id=user_id)

    Lobby.move(user_id, to_lobby_id=user_id)
    ws_controller.lobby_update([current_lobby, user_lobby])

    user = User.objects.get(pk=user_id)

    ws_controller.user_status_change(user)
    ws_controller.user_update(user)
    ws_controller.lobby_invites_update(current_lobby)

    return current_lobby


def lobby_invite(lobby_id: int, from_user_id: int, to_user_id: int) -> LobbyInvite:
    lobby = Lobby(owner_id=lobby_id)

    try:
        invite = lobby.invite(from_user_id, to_user_id)
        ws_controller.lobby_player_invite(invite)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return invite


def lobby_accept_invite(user: User, lobby_id: int, invite_id: str) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)
    was_solo = lobby.players_count == 1
    try:
        invite = LobbyInvite.get(lobby_id=lobby_id, invite_id=invite_id)
    except LobbyInviteException as exc:
        raise HttpError(400, str(exc))

    if user.id in lobby.players_ids:
        lobby.delete_invite(invite_id)
    else:
        try:
            lobby.move(user.id, lobby_id)
        except LobbyException as exc:
            raise HttpError(400, str(exc))

        ws_controller.lobby_update([lobby])
        ws_controller.user_status_change(user)
        ws_controller.lobby_invites_update(lobby)

        if was_solo:
            ws_controller.user_status_change(User.objects.get(pk=invite.from_id))

    return lobby


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


def lobby_leave(user: User) -> User:
    current_lobby = user.account.lobby
    user_lobby = Lobby(owner_id=user.id)
    lobbies_update = [current_lobby, user_lobby]
    new_lobby = Lobby.move(user.id, to_lobby_id=user.id)
    if new_lobby:
        lobbies_update.append(new_lobby)
        for user_id in new_lobby.players_ids:
            ws_controller.user_status_change(User.objects.get(pk=user_id))

    ws_controller.lobby_update(lobbies_update)
    ws_controller.lobby_invites_update(current_lobby, expired=bool(new_lobby))
    user = User.objects.get(pk=user.id)
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
            PreMatch.create(team.id, opponent.id)
            lobbies = team.lobbies + opponent.lobbies
            ws_controller.match_found(lobbies)

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


def match_player_lock_in(user: User, match_id: str):
    try:
        match = PreMatch.get_by_id(match_id)
    except PreMatchException:
        raise Http404()

    if user not in match.players:
        raise AuthenticationError()

    match.set_player_lock_in()
    if match.players_in >= PreMatchConfig.READY_PLAYERS_MIN:
        match.start_players_ready_countdown()


def match_player_ready(user: User, match_id: str):
    try:
        match = PreMatch.get_by_id(match_id)
    except PreMatchException:
        raise Http404()

    if user not in match.players:
        raise AuthenticationError()

    match.set_player_ready()
    if match.players_ready >= PreMatchConfig.READY_PLAYERS_MIN:
        pass
        # TODO create match in DB
        # (https://github.com/3C-gg/reload-backend/issues/241)

        # TODO start match on the FiveM server
        # (https://github.com/3C-gg/reload-backend/issues/243)
