import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.websocket import ws_update_user
from pre_matches.models import PreMatch, Team
from pre_matches.websocket import ws_pre_match_create

from . import models
from .websocket import ws_queue_tick, ws_update_lobby

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


def handle_match_found(team: Team, opponent: Team):
    lobbies = team.lobbies + opponent.lobbies

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
            return

        lobby.cancel_queue()
        ws_update_lobby(lobby)

    pre_match = PreMatch.create(
        team.id,
        opponent.id,
        lobbies[0].lobby_type,
        lobbies[0].mode,
    )
    ws_pre_match_create(pre_match)


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

        else:
            for team in unready_teams:
                if team.id != lobby_team.id:
                    players_length = team.players_count + lobby.players_count
                    if (
                        players_length <= settings.TEAM_READY_PLAYERS_MIN
                        and players_length > lobby_team.players_count
                    ):
                        if (
                            lobby.queue
                            and not lobby_team.pre_match_id
                            and not team.pre_match_id
                        ):
                            lobby_team.remove_lobby(lobby.id)
                            team.add_lobby(lobby.id)

    log_teaming_info()


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
    ws_update_lobby(lobby)
    ws_update_user(user)


@shared_task
def queue():
    handle_teaming()
    handle_matchmaking()
