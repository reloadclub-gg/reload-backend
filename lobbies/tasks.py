import time

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


def handle_match_found(team: Team, opponent: Team):
    lobbies = team.lobbies + opponent.lobbies
    for lobby in lobbies:
        lobby.cancel_queue()
        ws_update_lobby(lobby)

    pre_match = PreMatch.create(team.id, opponent.id)
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

        if not lobby_team:
            not_ready_teams = Team.get_all_not_ready()
            if len(not_ready_teams) > 0:
                for team in not_ready_teams:
                    if team.players_count + lobby.players_count <= lobby.max_players:
                        team.add_lobby(lobby.id)
            else:
                Team.create([lobby.id])


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
