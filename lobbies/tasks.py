import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.websocket import ws_update_user
from pre_matches.models import PreMatch, Team
from pre_matches.websocket import ws_pre_match_create

from . import models
from .websocket import ws_queue_tick, ws_update_lobby

User = get_user_model()


def handle_match_found(team: Team, opponent: Team):
    logging.info('handle_match_found')
    lobbies = team.lobbies + opponent.lobbies
    logging.info('lobbies')
    logging.info(lobbies)
    for lobby in lobbies:
        logging.info('lobby to cancel queue')
        logging.info(lobby)
        lobby.cancel_queue()
        ws_update_lobby(lobby)

    pre_match = PreMatch.create(team.id, opponent.id)
    ws_pre_match_create(pre_match)
    logging.info('pre_match')
    logging.info(pre_match.id)


def handle_matchmaking():
    logging.info('handle_matchmaking')
    ready_teams = Team.get_all_ready()
    logging.info('ready_teams')
    logging.info(ready_teams)
    if len(ready_teams) > 1:
        team = ready_teams[0]
        opponent = team.get_opponent_team()
        if opponent and opponent.ready:
            handle_match_found(team, opponent)


def handle_teaming():
    logging.info('handle_teaming')
    queued_lobbies = models.Lobby.get_all_queued()
    logging.info('queued lobbies')
    logging.info(queued_lobbies)
    logging.info('players queued')
    logging.info([lobby.players_ids for lobby in queued_lobbies])
    for lobby in queued_lobbies:
        logging.info('mm lobby')
        logging.info(lobby.id)
        ws_queue_tick(lobby)
        lobby_team = Team.get_by_lobby_id(lobby.id, fail_silently=True)
        logging.info('lobby team')
        logging.info(lobby_team)

        if not lobby_team:
            not_ready_teams = Team.get_all_not_ready()
            logging.info('not_ready_teams')
            logging.info(not_ready_teams)
            for team in not_ready_teams:
                logging.info('team lobby add')
                logging.info(team.players_count)
                logging.info(lobby.players_count)
                logging.info(lobby.max_players)
                if team.players_count + lobby.players_count <= lobby.max_players:
                    team.add_lobby(lobby.id)
                    break

            else:
                team = Team.create([lobby.id])
                logging.info('team created')
                logging.info(team.id)
                logging.info(team.ready)
                logging.info(Team.get_all_not_ready())


@shared_task
def clear_dodges():
    players = models.Player.get_all()
    last_week = timezone.now() - timezone.timedelta(weeks=1)
    for player in players:
        if player.latest_dodge and player.latest_dodge <= last_week:
            player.dodge_clear()


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
