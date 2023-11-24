import logging
import math
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja.errors import Http404, HttpError

from accounts.utils import hex_to_steamid64
from accounts.websocket import ws_update_user
from core.utils import get_full_file_path
from friends.websocket import ws_friend_update_or_create
from pre_matches.models import PreMatch

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


def notify_users(match):
    for player in match.players:
        ws_update_user(player.user)
        ws_friend_update_or_create(player.user)


def should_finish_match(is_overtime, scores):
    if is_overtime:
        diff = abs(scores[0] - scores[1])
        return diff >= 2
    else:
        return any(score >= settings.MATCH_ROUNDS_TO_WIN for score in scores)


def update_scores(match, teams_data, end_reason):
    team_scores = {team.name: team.score for team in teams_data}
    teams = models.MatchTeam.objects.filter(
        match=match,
        name__in=list(team_scores.keys()),
    )
    for idx, team in enumerate(teams):
        if idx == 0:
            if (
                end_reason != 6  # SURRENDER
                and team_scores[team.name] - team.score >= 2
                and team_scores[teams[1].name] <= teams[1].score
            ):
                logging.warning(
                    f'[update_scores] match {match.id}: team {team.name} '
                    f'{team_scores[team.name]} ({team.score})'
                )
                teams[1].score = team_scores[team.name]
                teams[1].save(update_fields=['score'])
                return teams[0].score, teams[1].score
        else:
            if (
                end_reason != 6  # SURRENDER
                and team_scores[team.name] - team.score >= 2
                and team_scores[teams[0].name] <= teams[0].score
            ):
                logging.warning(
                    f'[update_scores] match {match.id}: team {team.name}'
                    f'{team_scores[team.name]} ({team.score})'
                )
                teams[0].score = team_scores[team.name]
                teams[0].save(update_fields=['score'])
                return teams[0].score, teams[1].score

        team.score = team_scores[team.name]
        team.save(update_fields=['score'])

    return teams[0].score, teams[1].score


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

    try:
        with transaction.atomic():
            scores = update_scores(match, payload.teams, payload.end_reason)
            stats_payload = payload.teams[0].players + payload.teams[1].players
            handle_update_players_stats(stats_payload, match)

            if should_finish_match(payload.is_overtime, scores):
                match.finish()

            if payload.chat:
                match.chat = payload.chat
                match.save()
    except (IntegrityError, Exception) as e:
        logging.error(e)
        raise HttpError(400, _('Unable to update match.'))

    match.refresh_from_db()
    websocket.ws_match_update(match)

    if match.status == models.Match.Status.FINISHED:
        notify_users(match)


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
        pre_match = PreMatch.get_by_player_id(player.user.id)
        if pre_match:
            team1 = pre_match.teams[0]
            if team1:
                team1.delete()
            team2 = pre_match.teams[1]
            if team2:
                team2.delete()

            PreMatch.delete(pre_match.id)

        ws_update_user(player.user)
        ws_friend_update_or_create(player.user)
