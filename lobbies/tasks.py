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
    logging.info('')
    logging.info('-- handle_match_found start --')
    logging.info('')

    lobbies = team.lobbies + opponent.lobbies
    for lobby in lobbies:
        logging.info(f'[handle_match_found] lobby queue cancel: {lobby.id}')
        lobby.cancel_queue()
        ws_update_lobby(lobby)

    pre_match = PreMatch.create(team.id, opponent.id)
    ws_pre_match_create(pre_match)
    logging.info(f'[handle_match_found] pre_match: {pre_match.id}')
    players_ids = [player.id for player in pre_match.players]
    teams_ids = [team.id for team in pre_match.teams]
    logging.info(f'[handle_match_found] pre_match players: {players_ids}')
    logging.info(f'[handle_match_found] pre_match teams: {teams_ids}')
    logging.info(f'[handle_match_found] team1 ready: {team.ready}')
    logging.info(f'[handle_match_found] team2 ready: {opponent.ready}')
    logging.info('')
    logging.info('-- handle_match_found end --')
    logging.info('')


def handle_matchmaking():
    ready_teams = Team.get_all_ready()
    if len(ready_teams) > 1:
        logging.info('')
        logging.info('-- handle_matchmaking start --')
        logging.info('')
        team = ready_teams[0]
        logging.info(f'[handle_teaming] ready team: {team.id}')
        logging.info(f'[handle_teaming] team lobbies: {team.lobbies_ids}')
        opponent = team.get_opponent_team()
        logging.info(f'[handle_teaming] opponent team: {opponent.id}')
        logging.info(f'[handle_teaming] opponent team lobbies: {opponent.lobbies_ids}')
        logging.info(f'[handle_teaming] opponent team ready: {opponent.ready}')
        if opponent and opponent.ready:
            logging.info(f'[handle_teaming] match found: {team.id} x {opponent.id}')
            logging.info(
                f'[handle_teaming] match lobbies: {team.lobbies_ids} x {opponent.lobbies_ids}'
            )
            handle_match_found(team, opponent)

        logging.info('')
        logging.info('-- handle_matchmaking end --')
        logging.info('')


def handle_teaming():
    logging.info('')
    logging.info('-- handle_teaming start --')
    logging.info('')

    queued_lobbies = models.Lobby.get_all_queued()
    logging.info(f'[handle_teaming] queued_lobbies: {queued_lobbies}')

    for lobby in queued_lobbies:
        logging.info(f'[handle_teaming] lobby: {lobby.id}')
        logging.info(f'[handle_teaming] players: {lobby.players_ids}')
        ws_queue_tick(lobby)
        lobby_team = Team.get_by_lobby_id(lobby.id, fail_silently=True)
        logging.info(f'[handle_teaming] team: {lobby_team.id if lobby_team else None}')

        if not lobby_team:
            not_ready_teams = Team.get_all_not_ready()
            for team in not_ready_teams:
                if team.players_count + lobby.players_count <= lobby.max_players:
                    team.add_lobby(lobby.id)
                    logging.info(f'[handle_teaming] not ready team: {team.id}')
                    logging.info(f'[handle_teaming] lobby size: {lobby.players_count}')
                    logging.info(f'[handle_teaming] team size: {team.players_count}')
                    logging.info(f'[handle_teaming] team lobby add: {lobby.id}')
                    logging.info(f'[handle_teaming] team ready: {team.ready}')
                    logging.info(f'[handle_teaming] team lobbies: {team.lobbies_ids}')
                    break

            else:
                team = Team.create([lobby.id])
                logging.info(f'[handle_teaming] created team: {team.id}')

    logging.info('')
    logging.info('-- handle_teaming end --')
    logging.info('')


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
