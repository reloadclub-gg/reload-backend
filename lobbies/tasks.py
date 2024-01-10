import logging
from typing import List

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.websocket import ws_update_user
from pre_matches.api.controller import cancel_pre_match
from pre_matches.models import PreMatch, PreMatchException, Team
from pre_matches.websocket import ws_pre_match_create

from . import models
from .websocket import ws_queue_start, ws_queue_tick, ws_update_lobby

User = get_user_model()


def log_teaming_info():
    not_ready_teams = Team.get_all_not_ready()
    ready_teams = Team.get_all_ready()

    title_separator_line = "+" + "=" * 40
    separator_line = "+" + "-" * 40
    logging.info(title_separator_line)
    logging.info("| lobbies.tasks.handle_teaming")
    logging.info(title_separator_line)
    logging.info("| unready teams:")
    logging.info(separator_line)

    for team in not_ready_teams:
        for lobby in team.lobbies:
            logging.info(
                f"| team: {team.id} | lobby: {lobby.id} | players: {tuple(lobby.players_ids)}"
            )

    logging.info(separator_line)

    # Log para times prontos
    logging.info("| ready teams:")
    logging.info(separator_line)

    for team in ready_teams:
        for lobby in team.lobbies:
            logging.info(
                f"| team: {team.id} | lobby: {lobby.id} | players: {tuple(lobby.players_ids)}"
            )

    logging.info(separator_line)


def handle_match_found_checks(
    users: List[User],
    team: Team,
    opponent: Team,
    lobbies: List[models.Lobby],
):
    for user in users:
        if user.account.get_match() is not None or user.account.pre_match:
            logging.warning(
                f'[handle_match_found] match or pre_match already exists for player {user.id}'
            )
            team.delete()
            opponent.delete()
            return

    if len(lobbies) < 2:
        logging.warning(
            f'[handle_match_found] lobbies missing ({len(team.lobbies)}, {len(opponent.lobbies)})'
        )
        team.delete()
        opponent.delete()
        return

    if not all(lobby.max_players == lobbies[0].max_players for lobby in lobbies):
        logging.warning(
            '[handle_match_found] max_players diff '
            f'({",".join([lobby.max_players for lobby in lobbies])})'
        )
        team.delete()
        opponent.delete()
        return

    max_players = team.lobbies[0].max_players
    total_players = team.players_count + opponent.players_count

    if (
        total_players < settings.TEAM_READY_PLAYERS_MIN * 2
        or total_players > max_players * 2
    ):
        logging.warning(f'[handle_match_found] wrong players length: {total_players}')
        logging.warning(
            f'[handle_match_found] deleting teams ({team.id}, {opponent.id})'
        )
        team.delete()
        opponent.delete()
        return

    for lobby in lobbies:
        if not lobby.queue:
            logging.warning(f'[handle_match_found] lobby not queued: {lobby.id}')
            if lobby.id in team.lobbies_ids:
                team.remove_lobby(lobby.id)
            else:
                opponent.remove_lobby(lobby.id)

            return

        lobby.cancel_queue()
        ws_update_lobby(lobby)


def handle_match_found(team: Team, opponent: Team):
    lobbies = team.lobbies + opponent.lobbies
    user_ids = [player_id for lobby in lobbies for player_id in lobby.players_ids]
    users = User.objects.filter(id__in=user_ids)

    handle_match_found_checks(users, team, opponent, lobbies)

    try:
        pre_match = PreMatch.create(
            team.id,
            opponent.id,
            lobbies[0].lobby_type,
            lobbies[0].mode,
        )
        ws_pre_match_create(pre_match)

    except PreMatchException as e:
        players_count = team.players_count + opponent.players_count
        logging.warning(f'[handle_match_found] {e} ({players_count})')
        return


def handle_matchmaking():
    ready_teams = Team.get_all_ready()
    if len(ready_teams) > 1:
        team = ready_teams[0]
        opponent = team.get_opponent_team()
        if opponent and opponent.ready:
            handle_match_found(team, opponent)


def handle_teaming():
    queued_lobbies = models.Lobby.get_all_queued()

    for lobby in queued_lobbies:
        ws_queue_tick(lobby)
        lobby_team = Team.get_by_lobby_id(lobby.id, fail_silently=True)
        unready_teams = Team.get_all_not_ready()

        if not lobby_team:
            for team in unready_teams:
                if team.players_count + lobby.players_count <= lobby.max_players:
                    team.add_lobby(lobby.id)
                    break

            else:
                team = Team.create([lobby.id])

    log_teaming_info()


def handle_dodges(lobby: models.Lobby, ready_players_ids: List[int]) -> List[int]:
    dodged_players_ids = []
    for player_id in lobby.players_ids:
        if player_id not in ready_players_ids:
            dodge, created = models.PlayerDodges.objects.get_or_create(
                user_id=player_id
            )
            if not created:
                dodge.count += 1
                dodge.save()
            dodged_players_ids.append(player_id)

    return dodged_players_ids


def handle_cancel_pre_match(pre_match: PreMatch):
    # get ready_players_ids and lobbies before we delete pre_match keys from Redis
    ready_players_ids = [player.id for player in pre_match.players_ready]
    dodged_players_ids = []

    # restart queue for lobbies that were ready and handle dodges for the ones who aren't
    for lobby in pre_match.lobbies:
        if all(elem in ready_players_ids for elem in lobby.players_ids):
            ws_queue_start(lobby)
        else:
            dodged_players_ids = handle_dodges(lobby, ready_players_ids)

        ws_update_lobby(lobby)

    msg_type = None
    if len(dodged_players_ids) > 0:
        msg_type = 'dodge'

    cancel_pre_match(pre_match, msg_type, dodged_players_ids)


def handle_pre_matches():
    pre_matches = PreMatch.get_all()
    for pre_match in pre_matches:
        if (
            pre_match.countdown
            and pre_match.countdown < settings.MATCH_READY_COUNTDOWN_GAP
        ):
            handle_cancel_pre_match(pre_match)


@shared_task
def clear_dodges():
    last_week = timezone.now() - timezone.timedelta(
        seconds=settings.PLAYER_DODGES_EXPIRE_TIME
    )
    dodges = models.PlayerDodges.objects.filter(last_dodge_date__lte=last_week)
    dodges.update(count=0)


@shared_task
def end_player_restriction(user_id: int):
    user = User.objects.get(pk=user_id)
    lobby = user.account.lobby
    ws_update_user(user)
    if lobby:
        ws_update_lobby(lobby)


@shared_task
def queue():
    handle_pre_matches()
    handle_teaming()
    handle_matchmaking()
