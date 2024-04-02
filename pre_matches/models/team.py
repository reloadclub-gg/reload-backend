from __future__ import annotations

import logging
import random
import secrets
from math import ceil
from statistics import mean

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import redis_client_instance as cache
from lobbies.models import Lobby

User = get_user_model()


class TeamException(Exception):
    """
    Custom Team exception class.
    """

    pass


class TeamConfig:
    """
    Config class for the Team model.
    """

    CACHE_PREFIX: str = "__mm:team:"
    ID_SIZE: int = 16


class Team(BaseModel):
    """
    This model represents teams on Redis cache db.
    Teams are full lobbies that are queued.

    The Redis db keys from this model are described below:

    [set] __mm:team:[team_id] <lobby_ids>
    Stores a team.

    [key] __mm:team:[team_id]:ready 1
    If this key exists, the team is ready and able to find an
    oposing team to play against. A team is ready when it reaches
    the maximum numbers of players.

    [key] __mm:team:[team_id]:pre_match <pre_match_id>
    Stores a pre_match that team is on. It should not exists
    if team isn't in any pre_match.
    """

    id: str = None
    cache_key: str = None

    def __init__(self, **data):
        super().__init__(**data)
        self.id = self.id or secrets.token_urlsafe(TeamConfig.ID_SIZE)
        self.cache_key = self.cache_key or f"{TeamConfig.CACHE_PREFIX}{self.id}"

    @property
    def lobbies_ids(self) -> list:
        return sorted(list(map(int, cache.smembers(self.cache_key))))

    @property
    def players_count(self) -> int:
        """
        Return how many players are in all the team lobbies.
        """
        return sum(
            [Lobby(owner_id=lobby_id).players_count for lobby_id in self.lobbies_ids]
        )

    @property
    def ready(self) -> bool:
        """
        Return whether this team is ready to find a oposing team.
        """
        return self.players_count >= settings.TEAM_READY_PLAYERS_MIN

    @property
    def overall(self) -> int:
        """
        Return all lobbies overall.

        If there is only one lobby on team, then the overral will
        be the highest level among that lobby players (what is equal to lobby.overall).

        If there is more then one lobby, the overall will be the average between all lobbies.

        This is effective because if there is only one lobby, it means that is a pre builded lobby
        with friends, and thus we want to pair by the highest skilled/leveled player.
        """
        if len(self.lobbies_ids) > 0:
            return ceil(
                mean(
                    [Lobby(owner_id=lobby_id).overall for lobby_id in self.lobbies_ids]
                )
            )

    @property
    def min_max_overall_by_queue_time(self) -> tuple:
        """
        Return the minimum and maximum team overall that this team
        can team up or challenge.
        """

        if len(self.lobbies) <= 0 or self.overall is None:
            return None

        queue_times = [
            lobby.queue_time if lobby.queue_time else 0 for lobby in self.lobbies
        ]
        if len(queue_times) > 0:
            return 0, 30
            # elapsed_time = ceil(mean(queue_times))

            # if elapsed_time < 30:
            #     min = self.overall - 3 if self.overall > 3 else 0
            #     max = self.overall + 3
            # elif elapsed_time < 60:
            #     min = self.overall - 4 if self.overall > 4 else 0
            #     max = self.overall + 4
            # elif elapsed_time < 90:
            #     min = self.overall - 5 if self.overall > 5 else 0
            #     max = self.overall + 5
            # elif elapsed_time < 120:
            #     min = self.overall - 6 if self.overall > 6 else 0
            #     max = self.overall + 6
            # else:
            #     min = self.overall - 7 if self.overall > 7 else 0
            #     max = self.overall + 7

            # return min, max

    @property
    def lobbies(self) -> list[Lobby]:
        """
        Return lobbies.
        """
        return [Lobby(owner_id=lobby_id) for lobby_id in self.lobbies_ids]

    @property
    def mode(self) -> tuple:
        """
        Return team type and mode.
        """
        if len(self.lobbies) > 0:
            return self.lobbies[0].mode

    @property
    def name(self) -> str:
        """
        Return team name defined randomly between owners in lobbies
        """
        if len(self.lobbies) > 0:
            owners_ids = [lobby.owner_id for lobby in self.lobbies]
            owner_chosen_id = random.choice(owners_ids)
            return User.objects.get(pk=owner_chosen_id).steam_user.username

    @property
    def pre_match_id(self) -> str:
        return cache.get(f"{self.cache_key}:pre_match")

    @staticmethod
    def overall_match(team, lobby) -> bool:
        if team.min_max_overall_by_queue_time is not None:
            min_overall, max_overall = team.min_max_overall_by_queue_time
            return min_overall <= lobby.overall <= max_overall

        return False

    @staticmethod
    def get_all() -> list[Team]:
        """
        Fetch and return all Teams on Redis db.
        """
        keys = list(cache.scan_keys(f"{TeamConfig.CACHE_PREFIX}*"))
        if not keys:
            return []

        filtered_keys = [key for key in keys if len(key.split(":")) == 3]
        return [Team.get_by_id(key.split(":")[2]) for key in filtered_keys]

    @staticmethod
    def get_all_not_ready() -> list[Team]:
        """
        Fetch all non ready teams in Redis db.
        """
        teams = Team.get_all()
        not_ready = [
            team for team in teams if team and not team.ready and not team.pre_match_id
        ]
        return sorted(not_ready, key=lambda team: team.players_count, reverse=True)

    @staticmethod
    def get_all_ready() -> list[Team]:
        """
        Fetch all ready teams in Redis db.
        """
        teams = Team.get_all()
        return [team for team in teams if team and team.ready and not team.pre_match_id]

    @staticmethod
    def get_by_lobby_id(lobby_id: int, fail_silently=False) -> Team:
        """
        Searchs for a team given a lobby id.
        """
        team = next(
            (team for team in Team.get_all() if team and lobby_id in team.lobbies_ids),
            None,
        )
        if not team and not fail_silently:
            raise TeamException(_("Team not found."))

        return team

    @staticmethod
    def get_by_id(id: str, raise_error: bool = False) -> Team:
        """
        Searchs for a team given an id.
        """
        cache_key = f"{TeamConfig.CACHE_PREFIX}{id}"
        result = cache.smembers(cache_key)
        if not result:
            if raise_error:
                raise TeamException(_("Team not found."))
            return None

        return Team(id=id)

    @staticmethod
    def create(lobbies_ids: list) -> Team:
        """
        Create a Team in Redis cache db given a list of lobbies ids.
        """
        lobbies = [Lobby(owner_id=lobby_id) for lobby_id in lobbies_ids]
        max_players = [lobby.max_players for lobby in lobbies]
        players_count = sum([lobby.players_count for lobby in lobbies])

        if not max_players.count(max_players[0]) == len(max_players):
            raise TeamException(_("Lobbies have differents types or modes."))

        if players_count > max_players[0]:
            raise TeamException(_("Team players count exceeded."))

        if not all([lobby.queue for lobby in lobbies]):
            raise TeamException(_("Lobbies not queued"))

        team_id = secrets.token_urlsafe(TeamConfig.ID_SIZE)
        cache.sadd(f"{TeamConfig.CACHE_PREFIX}{team_id}", *lobbies_ids)
        return Team.get_by_id(team_id)

    def delete(self):
        """
        Delete team from Redis db.
        """
        keys = list(cache.scan_keys(f"{self.cache_key}:*"))
        if keys:
            cache.delete(*keys)

        cache.delete(self.cache_key)

    def add_lobby(self, lobby_id: int):
        """
        Add a lobby into a Team on Redis db.
        """
        lobby = Lobby(owner_id=lobby_id)

        if not lobby.queue:
            raise TeamException(_("Lobby not queued"))

        def transaction_operations(pipe, pre_result):
            if self.ready:
                raise TeamException(_("Team is full. Can't add a lobby."))
            pipe.sadd(self.cache_key, lobby_id)

        cache.protected_handler(
            transaction_operations,
            f"{lobby.cache_key}:players",
            f"{lobby.cache_key}:queue",
            f"{self.cache_key}",
            f"{self.cache_key}:pre_match",
            f"{self.cache_key}:ready",
        )

    def remove_lobby(self, lobby_id: int):
        """
        Remove a lobby from a Team on Redis db.
        If that team was ready, then it becomes not ready.
        """
        lobby = Lobby(owner_id=lobby_id)

        def transaction_operations(pipe, pre_result):
            if self.pre_match_id:
                raise TeamException(_("Can't remove a lobby while in pre_match."))
            cache.srem(self.cache_key, lobby_id)

        cache.protected_handler(
            transaction_operations,
            f"{lobby.cache_key}:players",
            f"{lobby.cache_key}:queue",
            f"{self.cache_key}",
            f"{self.cache_key}:pre_match",
            f"{self.cache_key}:ready",
        )

        if len(self.lobbies_ids) <= 1:
            logging.info(f"[team:remove_lobby] delete team {self.id}")
            self.delete()

    def handle_non_queued_lobbies(self):
        non_queued = [lobby for lobby in self.lobbies if not lobby.queue]
        for lobby in non_queued:
            self.remove_lobby(lobby.id)

        return non_queued

    def get_opponent_team(self):
        if self.handle_non_queued_lobbies():
            logging.info("[team:get_opponent_team] some lobby isn't queued, continue")
            return

        ready_teams = self.get_all_ready()
        for team in ready_teams:
            logging.info(f"[team:get_opponent_team] try team: {team.id}")
            if team.pre_match_id:
                logging.info("[team:get_opponent_team] is in pre_match, continue")
                continue

            if self.id == team.id:
                logging.info("[team:get_opponent_team] is same team, continue")
                continue

            if team.handle_non_queued_lobbies():
                logging.info(
                    "[team:get_opponent_team] some lobby isn't queued, continue"
                )
                continue

            if self.mode is None or self.mode != team.mode:
                logging.info("[team:get_opponent_team] mismatch type or mode, continue")
                continue

            if team.min_max_overall_by_queue_time is None or self.overall is None:
                logging.info("[team:get_opponent_team] overalls missing, continue")
                continue

            min_overall, max_overall = team.min_max_overall_by_queue_time
            if min_overall <= self.overall <= max_overall:
                logging.info(f"[team:get_opponent_team] found opponent: {team.id}")
                return team

            logging.info("[team:get_opponent_team] didn't match the overall, continue")
