import logging
import math
import time
from typing import List

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from ninja.errors import Http404, HttpError

from accounts.utils import hex_to_steamid64
from accounts.websocket import ws_update_status_on_friendlist, ws_update_user
from core.utils import get_full_file_path
from pre_matches.models import PreMatch

from .. import models, tasks, websocket
from . import schemas

User = get_user_model()


def __create_fivem_match(match: models.Match) -> models.Match:
    if settings.TEST_MODE or settings.FIVEM_MATCH_MOCKS_ON:
        status_code = 201 if settings.FIVEM_MATCH_MOCK_CREATION_SUCCESS else 400
        fivem_response = schemas.FivemResponseMock.from_orm(
            {"status_code": status_code}
        )
        time.sleep(settings.FIVEM_MATCH_MOCK_DELAY_CONFIGURE)
    else:
        server_url = f"http://{match.server.ip}:{match.server.api_port}/api/matches"
        payload = schemas.FivemMatchSchema.from_orm(match).dict()
        try:
            fivem_response = requests.post(
                server_url,
                json=payload,
                timeout=settings.FIVEM_MATCH_CREATION_RETRIES_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            fivem_response = schemas.FivemResponseMock.from_orm({"status_code": 400})
            logging.warning(f"[handle_create_fivem_match] {match.id}")
            return None

    return fivem_response


def __cancel_match(match_id: int):
    try:
        match = models.Match.objects.exclude(
            status__in=[models.Match.Status.CANCELLED, models.Match.Status.FINISHED]
        ).get(id=match_id)
    except models.Match.DoesNotExist:
        raise Http404

    match.cancel()
    websocket.ws_match_delete(match)


def __create_custom_match_teams_players(match, payload):
    team_a = match.matchteam_set.create(name="A", side=1)
    team_b = match.matchteam_set.create(name="B", side=2)

    for player_id in payload.def_players_ids:
        team_a.matchplayer_set.create(user_id=player_id)

    for player_id in payload.atk_players_ids:
        team_b.matchplayer_set.create(user_id=player_id)

    for player_id in payload.spec_players_ids:
        models.MatchPlayer.objects.create(user_id=player_id, match=match)


def __warmup_match(match):
    match.warmup()
    if settings.TEST_MODE or settings.FIVEM_MATCH_MOCKS_ON:
        if settings.FIVEM_MATCH_MOCK_START_SUCCESS:
            tasks.mock_fivem_match_start.apply_async(
                (match.id,),
                countdown=settings.FIVEM_MATCH_MOCK_DELAY_START,
                serializer="json",
            )
        else:
            tasks.mock_fivem_match_cancel.apply_async(
                (match.id,),
                countdown=settings.FIVEM_MATCH_MOCK_DELAY_START,
                serializer="json",
            )


def __ws_update_players(match):
    for match_player in match.players:
        ws_update_user(match_player.user)
        ws_update_status_on_friendlist(match_player.user)

    for spec in match.spec_players:
        ws_update_user(spec.user)
        ws_update_status_on_friendlist(spec.user)


def handle_update_players_stats(
    players_stats: List[schemas.MatchUpdatePlayerStats],
    match: models.Match,
):
    steamids64 = [
        hex_to_steamid64(player_stat.steamid) for player_stat in players_stats
    ]

    # Get all stats at once from the database
    all_stats = models.MatchPlayerStats.objects.exclude(player__team=None).filter(
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
            "kills",
            "hs_kills",
            "deaths",
            "assists",
            "damage",
            "shots_fired",
            "head_shots",
            "chest_shots",
            "other_shots",
            "firstkills",
            "defuses",
            "plants",
            "double_kills",
            "triple_kills",
            "quadra_kills",
            "aces",
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
        .select_related("team__match", "stats", "team")
        .order_by("-team__match__end_date")
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
                "id": match.id,
                "map_name": match.map.name,
                "map_image": (
                    get_full_file_path(match.map.thumbnail)
                    if match.map.thumbnail
                    else None
                ),
                "match_type": match.match_type,
                "game_mode": match.game_mode,
                "start_date": match.start_date.isoformat(),
                "end_date": match.end_date.isoformat(),
                "won": user_team.id == match.winner.id,
                "score": f"{user_team.score} - {opponent_team.score}",
                "stats": {
                    "kda": f"{player.stats.kills}/{player.stats.deaths}/{player.stats.assists}",
                    "kdr": player.stats.kdr,
                    "head_accuracy": math.ceil(player.stats.head_accuracy),
                    "adr": player.stats.adr,
                    "firstkills": player.stats.firstkills,
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
        ws_update_status_on_friendlist(player.user)


def should_finish_match(is_overtime, scores):
    if is_overtime:
        diff = abs(scores[0] - scores[1])
        return diff >= 2
    else:
        return any(score >= settings.MATCH_ROUNDS_TO_WIN for score in scores)


def update_scores(match, teams_data, end_reason):
    team_scores = {team.name: team.score for team in teams_data}
    team1 = models.MatchTeam.objects.get(match=match, name=teams_data[0].name)
    team2 = models.MatchTeam.objects.get(match=match, name=teams_data[1].name)

    if end_reason != 6:
        if teams_data[0].score - team1.score >= 2:
            logging.warning(
                f"[update_scores] match {match.id}: team {team1.name} "
                f"{team_scores[team1.name]} ({team1.score})"
            )

            team2.score = teams_data[0].score
            team2.save()
            return team1.score, team2.score

        if teams_data[1].score - team2.score >= 2:
            logging.warning(
                f"[update_scores] match {match.id}: team {team2.name} "
                f"{team_scores[team2.name]} ({team2.score})"
            )

            team1.score = teams_data[1].score
            team1.save()
            return team1.score, team2.score

    team1.score = teams_data[0].score
    team1.save()
    team2.score = teams_data[1].score
    team2.save()

    return team1.score, team2.score


def _fetch_match(match_id: int):
    forbidden_statuses = [models.Match.Status.CANCELLED, models.Match.Status.FINISHED]
    try:
        return models.Match.objects.exclude(status__in=forbidden_statuses).get(
            id=match_id
        )
    except models.Match.DoesNotExist:
        raise Http404


def update_match(match_id: int, payload: schemas.MatchUpdateSchema):
    match = _fetch_match(match_id)

    if payload.status == "running":
        try:
            match.start()
            websocket.ws_match_update(match)
        except ValidationError as exc:
            logging.warning(exc)

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
        raise HttpError(400, _("Unable to update match."))

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
        ws_update_status_on_friendlist(player.user)


def create_match(payload: schemas.MatchCreationSchema) -> models.Match:
    # TODO competitive match is being created on pre_match app controller
    # so we're gonna only create customs matches on this method for now.
    if payload.mode != models.Match.GameMode.CUSTOM:
        raise HttpError(400, _("invalid game mode."))

    server = models.Server.get_idle(server_type=models.Server.ServerType.SAFEZONE)
    if not server:
        raise HttpError(400, _("Servers full."))

    try:
        map = models.Map.objects.get(id=payload.map_id)
    except models.Map.DoesNotExist:
        raise Http404(_("Map not found."))

    match = models.Match.objects.create(
        game_mode=models.Match.GameMode.CUSTOM,
        server=server,
        map=map,
        restricted_weapon=payload.weapon if payload.weapon else None,
    )

    __create_custom_match_teams_players(match, payload)
    websocket.ws_match_create(match)

    fivem_response = __create_fivem_match(match)
    if fivem_response and fivem_response.status_code == 201:
        __warmup_match(match)
    else:
        __cancel_match(match.id)

    __ws_update_players(match)

    return match
