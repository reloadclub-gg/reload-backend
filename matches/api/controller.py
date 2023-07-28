from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ninja.errors import Http404

from accounts.utils import hex_to_steamid64
from accounts.websocket import ws_update_user
from friends.websocket import ws_friend_update_or_create

from .. import models, websocket
from . import schemas

User = get_user_model()


def handle_update_players_stats(
    players_stats: List[schemas.MatchUpdatePlayerStats],
    match: models.Match,
):
    steamids64 = [
        hex_to_steamid64(player_stat.steamid) for player_stat in players_stats
    ]

    # Get all stats at once from the database
    all_stats = models.MatchPlayerStats.objects.filter(
        player__user__account__steamid__in=steamids64,
        player__team__match=match,
    )

    # Create a mapping from steamid64 to stats object
    stats_by_steamid64 = {stat.player.user.account.steamid: stat for stat in all_stats}

    # Update stats objects
    for player_stats in players_stats:
        steamid64 = hex_to_steamid64(player_stats.steamid)
        stats = stats_by_steamid64.get(steamid64)

        # Update fields
        stats.kills += player_stats.kills
        stats.hs_kills += player_stats.headshot_kills
        stats.deaths += player_stats.deaths
        stats.assists += player_stats.assists
        stats.damage += player_stats.damage
        stats.shots_fired += player_stats.shots_fired
        stats.head_shots += player_stats.head_shots
        stats.chest_shots += player_stats.chest_shots
        stats.other_shots += player_stats.other_shots

        if player_stats.firstkill:
            stats.firstkills += 1

        if player_stats.defuse:
            stats.defuses += 1
        elif player_stats.plant:
            stats.plants += 1

        if player_stats.kills >= 2:
            stats.double_kills += 1

        if player_stats.kills >= 3:
            stats.triple_kills += 1

        if player_stats.kills >= 4:
            stats.quadra_kills += 1

        if player_stats.kills >= 5:
            stats.aces += 1

    # Save all stats objects at once
    models.MatchPlayerStats.objects.bulk_update(
        all_stats,
        [
            'kills',
            'hs_kills',
            'deaths',
            'assists',
            'damage',
            'shots_fired',
            'head_shots',
            'chest_shots',
            'other_shots',
            'firstkills',
            'defuses',
            'plants',
            'double_kills',
            'triple_kills',
            'quadra_kills',
            'aces',
        ],
    )


def get_user_matches(user: User, user_id: int = None) -> List[models.Match]:
    search_id = user.id if not user_id else user_id

    matches_ids = models.MatchPlayer.objects.filter(
        user=search_id,
        team__match__status=models.Match.Status.FINISHED,
    ).values_list('team__match', flat=True)
    return models.Match.objects.filter(id__in=matches_ids)


def get_match(user: User, match_id: int) -> models.Match:
    match = get_object_or_404(models.Match, id=match_id)
    if (
        match.status != models.Match.Status.FINISHED
        and user.id not in match.players.values_list('user', flat=True)
    ):
        raise Http404

    return match


def update_match(match_id: int, payload: schemas.MatchUpdateSchema):
    match = get_object_or_404(
        models.Match,
        id=match_id,
        status=models.Match.Status.RUNNING,
    )

    team_a, team_b = models.MatchTeam.objects.filter(match=match)

    team_a.score = payload.team_a_score
    team_a.save()

    team_b.score = payload.team_b_score
    team_b.save()

    handle_update_players_stats(payload.players_stats, match)

    if payload.is_overtime:
        diff = abs(payload.team_a_score - payload.team_b_score)
        if diff >= 2:
            match.finish()
    elif (
        payload.team_a_score >= settings.WIN_ROUNDS
        or payload.team_b_score >= settings.WIN_ROUNDS
    ):
        match.finish()

    match.refresh_from_db()
    websocket.ws_match_update(match)

    if match.status == models.Match.Status.FINISHED:
        for player in match.players:
            ws_update_user(player.user)
            ws_friend_update_or_create(player.user)


def cancel_match(match_id: int):
    match = get_object_or_404(
        models.Match,
        id=match_id,
        status__in=[models.Match.Status.RUNNING, models.Match.Status.LOADING],
    )

    match.cancel()
    websocket.ws_match_delete(match)
    for player in match.players:
        ws_update_user(player.user)
        ws_friend_update_or_create(player.user)
