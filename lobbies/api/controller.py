from typing import List

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja.errors import AuthenticationError, Http404, HttpError

from accounts.websocket import ws_update_user
from appsettings.services import maintenance_window
from core.websocket import ws_create_toast
from friends.tasks import send_user_update_to_friendlist
from friends.websocket import ws_friend_update_or_create
from pre_matches.models import Team

from .. import websocket
from ..models import Lobby, LobbyException, LobbyInvite, LobbyInviteException
from .schemas import LobbyInviteCreateSchema, LobbyUpdateSchema

User = get_user_model()


def handle_player_move(user: User, lobby_id: int, delete_lobby: bool = False) -> Lobby:
    old_lobby = user.account.lobby
    new_lobby = Lobby(owner_id=lobby_id)

    try:
        remnants_lobby = Lobby.move(user.id, to_lobby_id=lobby_id, remove=delete_lobby)
    except LobbyException as exc:
        raise exc

    # if we got remnants_lobby, means that player was owner
    # and there was other players left to move
    if remnants_lobby:
        handle_player_move_remnants(new_lobby, remnants_lobby, user, delete_lobby)

    # if we don't have remnants_lobby
    # and user is moving to a lobby that isn't its original lobby
    elif new_lobby.id != user.id:
        handle_player_move_other_lobby(new_lobby, old_lobby, user)

    # we don't have remnants_lobby and user isn't moving to another owner's lobby, so
    # it means that the user is moving FROM another owner's lobby back to its original lobby
    # so old lobby will never be empty, because it will always have its owner left behind
    else:
        handle_player_move_original_lobby(new_lobby, old_lobby, user, delete_lobby)

    return new_lobby


def handle_player_move_remnants(
    new_lobby: Lobby,
    remnants_lobby: Lobby,
    user: User,
    delete_lobby: bool,
):
    # update lobbies objects for remnants lobby players
    websocket.ws_update_lobby(remnants_lobby)

    # send a "leave" signal so FE can handle a more specific event if necessary
    websocket.ws_update_player(remnants_lobby, user, 'leave')

    # send a ws to expire all invites sent by the user
    # because the user left the old lobby, all invites he sent should expire
    # and players who received cannot join his old lobby anymore
    websocket.ws_expire_player_invites(user, sent=True)

    # send a ws to expire all invites sent by remnants players
    # because they left the old lobby, all invites sent by them should expire
    # and players who received cannot join the old lobby anymore
    players = User.objects.filter(id__in=remnants_lobby.players_ids)
    for player in players:
        websocket.ws_expire_player_invites(player, sent=True)
        # send user status update to its online friends
        ws_friend_update_or_create(player)

        # update user so FE can get its new status and lobby_id
        ws_update_user(player)

    # if new lobby has the user moved or nobody else, the latter indicates
    # that the lobby was removed, it means that user is returning to its original lobby
    if new_lobby.players_count <= 1:
        # if we receive delete_lobby == True, then we do nothing
        # because this user just got offline or else
        if not delete_lobby:
            # replace the lobby object on FE with the new one
            websocket.ws_update_lobby(new_lobby)

            # send user status update to its online friends
            ws_friend_update_or_create(user)

            # send user update to user, so it can update
            # its lobby_id and status
            ws_update_user(user)

    # if new lobby has other players
    # then user that just got moved
    else:
        # replace the lobby object on FE with the new one
        websocket.ws_update_lobby(new_lobby)

        # we send a "join" signal so FE can handle
        # a more specific event if necessary
        websocket.ws_update_player(new_lobby, user, 'join')

        for player_id in new_lobby.players_ids:
            player = User.objects.get(id=player_id)
            # send user status update to its online friends
            ws_friend_update_or_create(player)

            # update user so FE can get its new status and lobby_id
            ws_update_user(player)


def handle_player_move_other_lobby(new_lobby: Lobby, old_lobby: Lobby, user: User):
    websocket.ws_expire_player_invites(user, sent=True)
    ws_update_user(user)
    ws_friend_update_or_create(user)

    websocket.ws_update_lobby(new_lobby)
    websocket.ws_update_player(new_lobby, user, 'join')
    if new_lobby.players_count == 2:
        new_lobby_owner = User.objects.get(pk=new_lobby.owner_id)
        ws_update_user(new_lobby_owner)
        ws_friend_update_or_create(new_lobby_owner)

    websocket.ws_update_lobby(old_lobby)
    websocket.ws_update_player(old_lobby, user, 'leave')
    if old_lobby.players_count == 1:
        old_lobby_owner = User.objects.get(pk=old_lobby.owner_id)
        ws_update_user(old_lobby_owner)
        ws_friend_update_or_create(old_lobby_owner)


def handle_player_move_original_lobby(
    new_lobby: Lobby,
    old_lobby: Lobby,
    user: User,
    delete_lobby: bool = False,
):
    # send a ws to expire all invites sent by the user
    # because the user left the old lobby, all invites he sent should expire
    # and players who received cannot join his old lobby anymore
    websocket.ws_expire_player_invites(user, sent=True)

    # if we receive delete_lobby=True, it means that the system will delete that lobby,
    # so isn't necessary to send any websocket update
    if old_lobby.id != new_lobby.id:
        # replace the lobby object on FE with the new one
        # for those who were left in old lobby
        websocket.ws_update_lobby(old_lobby)

        # send a "leave" signal so FE can handle a more specific event if necessary
        websocket.ws_update_player(old_lobby, user, 'leave')

        # check if old lobby was left with just its owner, so we need
        # to update its owner as well because before this move he was
        # teaming and now he's  solo, and FE and their friends needs to know its new status
        if old_lobby.players_count == 1:
            old_lobby_owner = User.objects.get(id=old_lobby.owner_id)

            # send user status update to its online friends
            ws_friend_update_or_create(old_lobby_owner)

            # update user so FE can get its new status and lobby_id
            ws_update_user(old_lobby_owner)

        if not delete_lobby:
            # send user status update to its online friends
            ws_friend_update_or_create(user)

            # update user so FE can get its new status and lobby_id
            ws_update_user(user)

            # update lobby so FE can replace the lobby object with a new one
            websocket.ws_update_lobby(new_lobby)


def get_lobby(lobby_id: int) -> Lobby:
    # TODO: check if lobby exists
    return Lobby(owner_id=lobby_id)


def get_user_invites(
    user: User,
    sent: bool = False,
    received: bool = False,
) -> List[LobbyInvite]:
    invites_sent = LobbyInvite.get_by_from_user_id(user.id)
    invites_received = LobbyInvite.get_by_to_user_id(user.id)

    if sent:
        return invites_sent

    if received:
        return invites_received

    return invites_sent + invites_received


def get_invite(user: User, invite_id: str) -> LobbyInvite:
    try:
        from_id = int(invite_id.split(':')[0])
        to_id = int(invite_id.split(':')[1])
    except ValueError:
        raise HttpError(422, _('Invalid invite id'))

    if user.id not in [from_id, to_id]:
        raise AuthenticationError()

    try:
        invite = LobbyInvite.get_by_id(invite_id)
    except LobbyInviteException as e:
        raise Http404(e)

    return invite


def accept_invite(user: User, invite_id: str):
    if maintenance_window():
        raise HttpError(400, _('We are under maintenance. Try again later.'))

    invite = get_invite(user, invite_id)
    if user.id != invite.to_id:
        raise AuthenticationError()

    current_lobby = user.account.lobby
    new_lobby = Lobby(owner_id=invite.lobby_id)

    if current_lobby.id == new_lobby.id:
        return {'status': None}

    websocket.ws_delete_invite(invite, 'accepted')
    try:
        handle_player_move(user, new_lobby.id)
    except LobbyException as e:
        raise HttpError(400, e)
    return {'status': 'accepted'}


def refuse_invite(user: User, invite_id: str):
    if maintenance_window():
        raise HttpError(400, _('We are under maintenance. Try again later.'))

    invite = get_invite(user, invite_id)
    if user.id != invite.to_id:
        raise AuthenticationError()

    websocket.ws_delete_invite(invite, 'refused')
    lobby = Lobby(owner_id=invite.lobby_id)
    lobby.delete_invite(invite.id)
    websocket.ws_update_lobby(lobby)
    return {'status': 'refused'}


def delete_player(user: User, lobby_id: int, player_id: int) -> Lobby:
    lobby = get_lobby(lobby_id)

    if maintenance_window():
        raise HttpError(400, _('We are under maintenance. Try again later.'))

    if player_id == user.id and lobby.players_count == 1:
        return lobby

    if player_id == user.id:
        try:
            return handle_player_move(user, user.id)
        except LobbyException as e:
            raise HttpError(400, e)
    elif user.id != lobby.owner_id:
        raise AuthenticationError()
    else:
        player = User.objects.get(pk=player_id)
        try:
            handle_player_move(player, player.id)
        except LobbyException as e:
            raise HttpError(400, e)
        ws_create_toast(
            _('{} kicked you from lobby.').format(user.account.username),
            user_id=player_id,
        )

    return lobby


def update_lobby(user: User, lobby_id: int, payload: LobbyUpdateSchema) -> Lobby:
    lobby = get_lobby(lobby_id)
    updated = False

    if payload.start_queue:
        updated = True
        if maintenance_window():
            raise HttpError(400, _('We are under maintenance. Try again later.'))

        if user.id != lobby.owner_id:
            raise AuthenticationError()

        try:
            lobby.start_queue()
        except LobbyException as e:
            raise HttpError(400, e)

    elif payload.cancel_queue:
        updated = True
        lobby.cancel_queue()
        team = Team.get_by_lobby_id(lobby_id, fail_silently=True)
        if team:
            team.remove_lobby(lobby_id)

    if updated:
        websocket.ws_update_lobby(lobby)

        lobby_players = User.objects.filter(id__in=lobby.players_ids)
        for player in lobby_players:
            ws_update_user(player)
            ws_friend_update_or_create(player)
            send_user_update_to_friendlist.delay(player.id)
            websocket.ws_expire_player_invites(player)

    return lobby


def create_invite(user: User, payload: LobbyInviteCreateSchema):
    if maintenance_window():
        raise HttpError(400, _('We are under maintenance. Try again later.'))

    lobby = get_lobby(payload.lobby_id)

    if user.id != payload.from_user_id or user.id not in lobby.players_ids:
        raise AuthenticationError()

    try:
        invite = lobby.invite(payload.from_user_id, payload.to_user_id)
    except LobbyException as exc:
        raise HttpError(400, exc)

    websocket.ws_create_invite(invite)
    websocket.ws_update_lobby(lobby)
    return invite
