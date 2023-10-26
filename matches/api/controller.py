import math
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja.errors import Http404

from accounts.utils import hex_to_steamid64
from accounts.websocket import ws_update_user
from core.utils import get_full_file_path
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

        if player_stats.kills >= 5:
            stats.aces += 1
        elif player_stats.kills >= 4:
            stats.quadra_kills += 1
        elif player_stats.kills >= 3:
            stats.triple_kills += 1
        elif player_stats.kills >= 2:
            stats.double_kills += 1

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


def get_user_matches(
    user: User, user_id: int = None
) -> List[schemas.MatchListItemSchema]:
    search_id = user.id if not user_id else user_id

    match_players = (
        models.MatchPlayer.objects.filter(
            user_id=search_id, team__match__status=models.Match.Status.FINISHED
        )
        .select_related('team__match', 'stats', 'team')
        .order_by('-team__match__end_date')
    )

    response = []
    for player in match_players:
        match = player.team.match
        user_team = player.team
        opponent_team = (
            match.team_a if user_team.id == match.team_b.id else match.team_b
        )

        response.append(
            {
                'id': match.id,
                'map_name': match.map.name,
                'map_image': get_full_file_path(match.map.thumbnail)
                if match.map.thumbnail
                else None,
                'game_type': match.game_type,
                'start_date': match.start_date.isoformat(),
                'end_date': match.end_date.isoformat(),
                'won': user_team.id == match.winner.id,
                'score': f'{user_team.score} - {opponent_team.score}',
                'stats': {
                    'kda': f'{player.stats.kills}/{player.stats.deaths}/{player.stats.assists}',
                    'kdr': player.stats.kdr,
                    'head_accuracy': math.ceil(player.stats.head_accuracy),
                    'adr': player.stats.adr,
                    'firstkills': player.stats.firstkills,
                },
            }
        )

    return response


def get_match(user: User, match_id: int) -> models.Match:
    match = get_object_or_404(
        models.Match,
        ~Q(status=models.Match.Status.CANCELLED),
        id=match_id,
    )
    if match.status in [
        models.Match.Status.LOADING,
        models.Match.Status.WARMUP,
        models.Match.Status.RUNNING,
    ]:
        if not match.players.filter(user=user.id).exists():
            raise Http404

    return match


def update_match(match_id: int, payload: schemas.MatchUpdateSchema):
    forbidden_statuses = [models.Match.Status.CANCELLED, models.Match.Status.FINISHED]
    try:
        match = models.Match.objects.exclude(status__in=forbidden_statuses).get(
            id=match_id
        )
    except models.Match.DoesNotExist:
        raise Http404

    if payload.status == 'running':
        match.start()
        websocket.ws_match_update(match)
        return

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
        payload.team_a_score >= settings.MATCH_ROUNDS_TO_WIN
        or payload.team_b_score >= settings.MATCH_ROUNDS_TO_WIN
    ):
        match.finish()

    if payload.chat:
        match.chat = payload.chat
        match.save()

    match.refresh_from_db()
    websocket.ws_match_update(match)

    if match.status == models.Match.Status.FINISHED:
        for player in match.players:
            ws_update_user(player.user)
            ws_friend_update_or_create(player.user)


def cancel_match(match_id: int):
    try:
        match = models.Match.objects.exclude(
            status__in=[models.Match.Status.CANCELLED, models.Match.Status.FINISHED]
        ).get(id=match_id)
    except models.Match.DoesNotExist:
        raise Http404

    match.cancel()
    websocket.ws_match_delete(match)
    for player in match.players:
        ws_update_user(player.user)
        ws_friend_update_or_create(player.user)
