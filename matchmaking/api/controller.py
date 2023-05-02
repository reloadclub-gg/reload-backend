from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja.errors import AuthenticationError, Http404, HttpError

from matches.models import Match, MatchPlayer, Server
from notifications.models import Notification
from websocket.tasks import (
    lobby_invites_update_task,
    lobby_player_invite_task,
    lobby_player_refuse_invite_task,
    lobby_update_task,
    match_task,
    pre_match_task,
    send_notification_task,
    user_status_change_task,
    user_update_task,
)

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


def lobby_move(user: User, lobby_id: int, inviter_user: User = None) -> Lobby:
    old_lobby = user.account.lobby
    new_lobby = Lobby(owner_id=lobby_id)
    lobbies_update = [old_lobby.id, new_lobby.id]
    update_inviter_status = new_lobby.players_count == 1

    try:
        derived_lobby = Lobby.move(user.id, to_lobby_id=lobby_id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    if derived_lobby:
        lobbies_update.append(derived_lobby.id)

    lobby_update_task.delay(lobbies_update)
    user_status_change_task.delay(user.id)

    if old_lobby.players_count == 1 or (
        not derived_lobby and old_lobby.owner_id == user.id
    ):
        if old_lobby.owner_id != user.id:
            user_status_change_task.delay(old_lobby.owner_id)

    if derived_lobby and derived_lobby.players_count == 1:
        user_status_change_task.delay(derived_lobby.owner_id)

    if update_inviter_status:
        user_status_change_task.delay(new_lobby.owner_id)

    user_update_task.delay(user.id)
    if inviter_user:
        user_update_task.delay(inviter_user.id)

    return new_lobby


def lobby_remove_player(user_id: int, lobby_id: int) -> Lobby:
    user = User.objects.get(pk=user_id)
    from_lobby = Lobby(owner_id=lobby_id)
    to_lobby = Lobby(owner_id=user_id)

    if user_id not in from_lobby.players_ids:
        raise HttpError(400, _('User must be in provided lobby to leave from it.'))

    return lobby_move(user, to_lobby.id)


def lobby_invite(lobby_id: int, from_user_id: int, to_user_id: int) -> LobbyInvite:
    lobby = Lobby(owner_id=lobby_id)

    try:
        invite = lobby.invite(from_user_id, to_user_id)
        lobby_player_invite_task.delay(lobby_id, invite.id)
        from_user_username = User.objects.get(pk=from_user_id).steam_user.username
        notification = User.objects.get(pk=to_user_id).account.notify(
            _(f'{from_user_username} invited you to a group.'), from_user_id
        )
        send_notification_task.delay(notification.id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    return invite


def lobby_refuse_invite(lobby_id: int, invite_id: str) -> LobbyInvite:
    try:
        invite = LobbyInvite.get(lobby_id, invite_id)
        lobby_player_refuse_invite_task.delay(lobby_id, invite_id)
        from_user_username = User.objects.get(pk=invite.to_id).steam_user.username
        notification = User.objects.get(pk=invite.from_id).account.notify(
            _(f'{from_user_username} refused your invite.'), invite.to_id
        )
        send_notification_task.delay(notification.id)
    except (LobbyException, LobbyInviteException) as exc:
        raise HttpError(400, str(exc))


def lobby_change_type_and_mode(
    lobby_id: int, lobby_type: str, lobby_mode: int, user: User
) -> Lobby:
    if user.account.match:
        raise HttpError(403, _('Can\'t change lobby mode or type while in a match.'))

    lobby = Lobby(owner_id=lobby_id)

    try:
        lobby.set_type(lobby_type)
        lobby.set_mode(lobby_mode)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    lobby_update_task.delay([lobby.id])

    return lobby


def lobby_enter(user: User, lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)

    try:
        Lobby.move(user.id, lobby_id)
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    lobby_update_task.delay([lobby.id])
    user_status_change_task.delay(user.id)
    lobby_invites_update_task.delay(lobby.id)

    lobby_players = [User.objects.get(pk=player_id) for player_id in lobby.players_ids]
    for player in lobby_players:
        user_status_change_task.delay(player.id)
        user_update_task.delay(player.id)

    return lobby


def set_public(lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)
    lobby.set_public()
    lobby_update_task.delay([lobby.id])

    return lobby


def set_private(lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)
    lobby.set_private()
    lobby_update_task.delay([lobby.id])

    return lobby


def lobby_accept_invite(user: User, lobby_id: int, invite_id: str) -> Lobby:
    current_lobby = user.account.lobby
    new_lobby = Lobby(owner_id=lobby_id)

    if current_lobby.id == new_lobby.id:
        raise HttpError(400, _('Can\'t accept an invite from the same lobby.'))

    try:
        lobby_invite = LobbyInvite.get(lobby_id=lobby_id, invite_id=invite_id)
    except LobbyInviteException as exc:
        raise HttpError(400, str(exc))

    if user.id in new_lobby.players_ids:
        new_lobby.delete_invite(invite_id)
        return new_lobby

    inviter = User.objects.get(pk=lobby_invite.from_id)
    lobby_move(user, new_lobby.id, inviter_user=inviter)

    from_user_username = User.objects.get(pk=user.id).steam_user.username
    notification = User.objects.get(pk=inviter.id).account.notify(
        _(f'{from_user_username} accepted your invite and joined your group.'), user.id
    )
    send_notification_task.delay(notification.id)
    return new_lobby


def lobby_leave(user: User) -> Lobby:
    user = User.objects.get(pk=user.id)
    to_lobby = Lobby(owner_id=user.id)

    return lobby_move(user, to_lobby.id)


def lobby_start_queue(lobby_id: int, user: User) -> Lobby:
    if user.account.match:
        raise HttpError(403, _('Can\'t start queue while in a match.'))

    lobby = Lobby(owner_id=lobby_id)

    try:
        lobby.start_queue()
    except LobbyException as exc:
        raise HttpError(400, str(exc))

    lobby_update_task.delay([lobby.id])
    lobby_invites_update_task.delay(lobby.id, expired=True)
    for invite in lobby.invites:
        lobby.delete_invite(invite.id)
    for user_id in lobby.players_ids:
        user_status_change_task.delay(user_id)

    team = Team.find(lobby) or Team.build(lobby)
    if team and team.ready:
        opponent = team.get_opponent_team()
        if opponent:
            lobbies = team.lobbies + opponent.lobbies
            for lobby in lobbies:
                lobby.cancel_queue()
                lobby_update_task.delay([lobby.id for lobby in lobbies])

            pre_match = PreMatch.create(team.id, opponent.id)
            pre_match_task.delay(pre_match.id)
            for user in pre_match.players:
                user_status_change_task.delay(user.id)

    return lobby


def lobby_cancel_queue(lobby_id: int) -> Lobby:
    lobby = Lobby(owner_id=lobby_id)
    lobby.cancel_queue()

    lobby_update_task.delay([lobby.id])
    for user_id in lobby.players_ids:
        user_status_change_task.delay(user_id)

    team = Team.get_by_lobby_id(lobby_id, fail_silently=True)
    if team:
        team.remove_lobby(lobby_id)

    return lobby


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
