import time
from typing import List

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import activate
from django.utils.translation import gettext as _

from accounts.websocket import ws_update_user
from core.utils import send_mail
from core.websocket import ws_create_toast
from friends.websocket import ws_friend_update_or_create
from lobbies.models import Lobby, PlayerDodges
from lobbies.websocket import ws_queue_start, ws_update_lobby
from matches.models import Match, Server

from . import models, websocket

User = get_user_model()


def get_match(pre_match_id: int) -> models.PreMatch:
    try:
        return models.PreMatch.get_by_id(pre_match_id)
    except models.PreMatchException:
        # we have deleted the pre_match already in favor of a match
        return None


def handle_cancel_match_ws(pre_match: models.PreMatch):
    websocket.ws_pre_match_delete(pre_match)
    for player in pre_match.players:
        ws_update_user(player)
        ws_friend_update_or_create(player)


def handle_delete_from_cache(team1: models.Team, team2: models.Team, pre_match_id: int):
    models.PreMatch.delete(pre_match_id)
    team1.delete()
    team2.delete()


def handle_dodges(lobby: Lobby, ready_players_ids: List[int]):
    msg = _(
        'Some players in your lobby were not ready before the'
        'timer ran out and the match was cancelled. The recurrence'
        'of this conduct may result in restrictions.'
    )

    for player_id in lobby.players_ids:
        ws_create_toast(msg, 'warning', user_id=player_id)
        if player_id not in ready_players_ids:
            dodge, created = PlayerDodges.objects.get_or_create(user_id=player_id)
            if not created:
                dodge.count += 1
                dodge.save()


@shared_task
def cancel_match_after_countdown(
    pre_match_id: int,
    lang: str = None,
    run_once: bool = False,
):
    pre_match = get_match(pre_match_id)
    if not pre_match or pre_match.status == models.PreMatch.Status.READY:
        return

    lang and activate(lang)

    if (
        pre_match.countdown
        and pre_match.countdown < models.PreMatch.Config.READY_COUNTDOWN_GAP
    ):
        team1 = pre_match.teams[0]
        team2 = pre_match.teams[1]
        lobbies = team1.lobbies + team2.lobbies

        # send ws call to lobbies to cancel that match
        handle_cancel_match_ws(pre_match)

        # get ready_players_ids before we delete pre_match keys from Redis
        ready_players_ids = [player.id for player in pre_match.players_ready]

        # delete the pre_match and teams from Redis
        handle_delete_from_cache(team1, team2, pre_match_id)

        # re-start queue for lobbies which all players accepted
        for lobby in lobbies:
            if all(elem in ready_players_ids for elem in lobby.players_ids):
                ws_queue_start(lobby)
            else:
                handle_dodges(lobby, ready_players_ids)

            ws_update_lobby(lobby)
    elif not run_once:
        # schedule this task again two seconds later
        time.sleep(2)
        return cancel_match_after_countdown(pre_match.id)


@shared_task
def send_server_almost_full_mail(name: str):
    server = Server.objects.get(name=name)
    running_matches = server.match_set.filter(
        status__in=[
            Match.Status.RUNNING,
            Match.Status.LOADING,
            Match.Status.WARMUP,
        ]
    ).count()

    send_mail(
        settings.ADMINS,
        'Servidor quase cheio',
        f'O servidor {server.name} ({server.ip}) está quase cheio: {running_matches}',
    )


@shared_task
def send_servers_full_mail():
    running_matches = Match.objects.filter(
        status__in=[
            Match.Status.RUNNING,
            Match.Status.LOADING,
            Match.Status.WARMUP,
        ]
    ).count()

    send_mail(
        settings.ADMINS,
        'Servidores cheios',
        f'Todos os servidores estão cheios. Total de partidas: {running_matches}',
    )
