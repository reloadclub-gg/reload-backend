from __future__ import annotations

import random
from typing import Dict, List

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from pydantic import BaseModel

from appsettings.services import (
    lobby_overall_range,
    lobby_time_to_increase_overall_range,
)
from core.models import Q, RedisHashModel
from core.redis import redis_client_instance as cache
from core.utils import str_to_timezone

User = get_user_model()


class LobbyException(Exception):
    pass


class LobbyInviteException(Exception):
    pass


class Lobby(BaseModel):
    owner_id: int
    mode: str = 'competitive'
    is_public: bool = False
    invites_ids: List[int] = []
    seats: Dict[int, int] = {}
    players_ids: List[int] = []

    class Config:
        CACHE_PREFIX: str = '__mm:lobby'
        MAX_SEATS: dict = {
            'competitive': 5,
            'custom': 15,  # 10 players + 5 specs
            'tdm': 5,
        }

    class ModeChoices:
        COMPETITIVE: str = 'competitive'
        CUSTOM: str = 'custom'
        TDM: str = 'tdm'

    @property
    def cache_key(self) -> str:
        return f'{self.Config.CACHE_PREFIX}:{self.owner_id}'

    @property
    def id(self) -> int:
        return self.owner_id

    @property
    def max_seats(self) -> int:
        return Lobby.Config.MAX_SEATS.get(self.mode)

    @property
    def players(self) -> list:
        return [User.objects.get(id=id) for id in self.players_ids]

    @property
    def is_queued(self) -> bool:
        queue_cache_key = f'{self.cache_key}:queue'
        return bool(cache.get(queue_cache_key))

    @property
    def queue_time(self) -> int:
        if self.is_queued:
            queue_start_time = str_to_timezone(cache.get(f'{self.cache_key}:queue'))
            return (timezone.now() - queue_start_time).seconds

    @property
    def overall(self) -> int:
        return max(
            list(
                User.objects.filter(id__in=self.players_ids).values_list(
                    'account__level', flat=True
                )
            )
            or [0]
        )

    @property
    def team_id(self):
        return cache.get(f'{self.cache_key}:team_id')

    @property
    def pre_match_id(self):
        return cache.get(f'{self.cache_key}:pre_match_id')

    def __start_queue(self):
        cache.set(f'{self.cache_key}:queue', timezone.now().isoformat())

    def __stop_queue(self):
        cache.delete(f'{self.cache_key}:queue')

    def save(self) -> Lobby:
        if self.pre_match_id:
            raise LobbyException(_('Can\'t perform this action while in match.'))

        def transaction_operations(pipe, _):
            pipe.hmset(
                self.cache_key,
                {'mode': self.mode, 'is_public': str(self.is_public)},
            )

            pipe.delete(f'{self.cache_key}:players_ids')
            if self.players_ids:
                pipe.sadd(f'{self.cache_key}:players_ids', *self.players_ids)

            pipe.delete(f'{self.cache_key}:invites_ids')
            if self.invites_ids:
                pipe.sadd(f'{self.cache_key}:invites_ids', *self.invites_ids)

        cache.protected_handler(
            transaction_operations,
            self.cache_key,
            f'{self.cache_key}:players_ids',
            f'{self.cache_key}:invites_ids',
        )

        return self

    def add_player(self, player_id: int):
        if player_id in self.players_ids:
            raise LobbyException(_('Player already in the lobby.'))

        if len(self.players_ids) == self.max_seats:
            raise LobbyException(_('Lobby is full.'))

        if not self.is_public and player_id != self.owner_id:
            invites = LobbyInvite.get_by_lobby_id(self.id)
            is_invited = any(invite.to_player_id == player_id for invite in invites)
            if not is_invited:
                raise LobbyException(_('Player must be invited.'))

        self.players_ids.append(player_id)
        self.save()

    def remove_player(self, player_id: int) -> Lobby:
        if player_id not in self.players_ids:
            raise LobbyException(_('Player not found.'))

        self.players_ids = [id for id in self.players_ids if id != player_id]
        self.save()

    def update_queue(self, action: str):
        if self.pre_match_id:
            raise LobbyException(_('Can\'t perform this action while in match.'))

        if self.mode == Lobby.ModeChoices.CUSTOM:
            raise LobbyException(
                _('Can\'t perform this action with current lobby mode.')
            )

        available_actions = ['start', 'stop']
        if action not in available_actions:
            raise LobbyException(_('Queues can only be started or stoped.'))

        if action == 'start':
            self.__start_queue()
        else:
            self.__stop_queue()

    def update_mode(self, mode: str):
        available_modes = [Lobby.ModeChoices.COMPETITIVE, Lobby.ModeChoices.CUSTOM]
        if mode not in available_modes:
            raise LobbyException(_(f'Mode must be {" or ".join(available_modes)}.'))

        if mode == self.mode:
            return

        if (
            mode == Lobby.ModeChoices.COMPETITIVE
            and len(self.players_ids) > Lobby.Config.COMP_MAX_SEATS
        ):
            raise LobbyException(_('Too many players to change lobby mode.'))

        self.mode = mode
        self.save()

    def get_queue_overall_range(self) -> tuple:
        if not self.is_queued:
            raise LobbyException(_('Lobby must be queued.'))

        elapsed_time = int(self.queue_time)
        time_range = lobby_time_to_increase_overall_range()
        overall_range = lobby_overall_range()

        for i in range(len(time_range)):
            if elapsed_time < time_range[i]:
                min_overall = max(self.overall - overall_range[i], 0)
                max_overall = self.overall + overall_range[i]
                return min_overall, max_overall

        min_overall = max(self.overall - overall_range[-1], 0)
        max_overall = self.overall + overall_range[-1]

        return min_overall, max_overall

    def delete(self):
        if self.pre_match_id:
            raise LobbyException(_('Can\'t perform this action while in match.'))

        for invite_id in self.invites_ids:
            try:
                invite = LobbyInvite.get(invite_id)
                invite.delete()
            except LobbyInviteException as exc:
                raise exc

        keys = list(cache.scan_keys(f'{self.cache_key}:*'))

        def transaction_operations(pipe, _):
            pipe.delete(*keys)
            pipe.delete(self.cache_key)

        cache.protected_handler(transaction_operations, self.cache_key, *keys)

    def expire_invites(self):
        for invite_id in self.invites_ids:
            try:
                invite = LobbyInvite.get(invite_id)
                invite.delete()
            except LobbyInviteException as exc:
                raise exc

    def update_visibility(self, visibility: str = 'private'):
        available_visibilities = ['public', 'private']
        if visibility not in available_visibilities:
            raise LobbyException(
                _(f'Visibility must be {(" or ").join(available_visibilities)}')
            )

        if visibility == 'public':
            self.is_public = True
        else:
            self.is_public = False

        self.save()

    @staticmethod
    def load(lobby_key: str) -> Lobby:
        owner_id = int(lobby_key.split(':')[2])

        players_ids = cache.smembers(f'{lobby_key}:players_ids')
        invites_ids = cache.smembers(f'{lobby_key}:invites_ids')

        return Lobby(
            owner_id=owner_id,
            mode=cache.hget(lobby_key, 'mode'),
            is_public=cache.hget(lobby_key, 'is_public') == 'True',
            players_ids=players_ids,
            invites_ids=invites_ids,
        )

    @staticmethod
    def get(owner_id: int, fail_silently: bool = False) -> Lobby:
        lobby_key = f'{Lobby.Config.CACHE_PREFIX}:{owner_id}'
        model = cache.hgetall(lobby_key)
        if model:
            return Lobby.load(lobby_key)

        if not fail_silently:
            raise LobbyException(_('Lobby not found.'))

    @staticmethod
    def get_by_player_id(player_id: int, fail_silently: bool = False) -> Lobby:
        keys = list(cache.scan_keys(f'{Lobby.Config.CACHE_PREFIX}:*:players_ids'))
        for key in keys:
            if str(player_id) in cache.smembers(key):
                lobby_key = ':'.join(key.split(':')[:-1])
                return Lobby.load(lobby_key)

        if not fail_silently:
            raise LobbyException(_('Lobby not found.'))

    @staticmethod
    def move_player_checks(player_id: int, from_lobby: Lobby, to_lobby: Lobby):
        if not from_lobby or not to_lobby:
            raise LobbyException(_('Lobby not found.'))

        if from_lobby.pre_match_id or to_lobby.pre_match_id:
            raise LobbyException(_('Can\'t perform this action while in match.'))

        if player_id not in from_lobby.players_ids:
            raise LobbyException(_('Player isn\'t in the specified lobby.'))

    @staticmethod
    def move_player(player_id: int, to_lobby_owner_id: int) -> tuple:
        from_lobby = Lobby.get_by_player_id(player_id)
        to_lobby = Lobby.get(to_lobby_owner_id)

        Lobby.move_player_checks(player_id, from_lobby, to_lobby)
        from_lobby.remove_player(player_id)
        remaining_lobby = None

        if player_id == from_lobby.owner_id and len(from_lobby.players_ids) > 0:
            new_owner_id = random.choice(from_lobby.players_ids)
            remaining_lobby = Lobby.get(new_owner_id)
            remaining_lobby.players_ids = from_lobby.players_ids
            from_lobby.players_ids = []
            from_lobby.save()
            remaining_lobby.save()

        if from_lobby.owner_id == to_lobby.owner_id:
            to_lobby = from_lobby

        to_lobby.add_player(player_id)
        return (from_lobby, to_lobby, remaining_lobby)

    @staticmethod
    def create(owner_id: int, mode: str = 'competitive', **kwargs) -> Lobby:
        mode_choices = [Lobby.ModeChoices.COMPETITIVE, Lobby.ModeChoices.CUSTOM]
        if mode not in mode_choices:
            raise LobbyException(_(f'Mode must be : {" or ".join(mode_choices)}.'))

        exists = Lobby.get_by_player_id(owner_id, fail_silently=True)
        if exists:
            raise LobbyException(_('Player already have a lobby.'))

        lobby = Lobby(owner_id=owner_id, mode=mode, players_ids=[owner_id])
        return lobby.save()

    @staticmethod
    def get_all_queued():
        keys = cache.scan_keys(f'{Lobby.Config.CACHE_PREFIX}:*:queue')
        queued = []
        for key in keys:
            queued.append(Lobby.get(int(key.split(':')[2])))

        return queued

    @staticmethod
    def cancel_queues():
        queued = Lobby.get_all_queued()
        for lobby in queued:
            lobby.update_queue('stop')


class LobbyInvite(RedisHashModel):
    id: int
    lobby_id: int
    from_player_id: int
    to_player_id: int

    class Config:
        CACHE_PREFIX: str = '__mm:invite'
        EXPIRE_TIME: int = 60  # in seconds

    @property
    def cache_key(self) -> str:
        return f'{self.Config.CACHE_PREFIX}:{self.id}'

    def save(self) -> LobbyInvite:
        def transaction_operations(pipe, _):
            pipe.hmset(
                self.cache_key,
                {
                    'id': self.id,
                    'from_player_id': self.from_player_id,
                    'to_player_id': self.to_player_id,
                    'lobby_id': self.lobby_id,
                },
            )

            # We always need to run a bg task to delete the invite and remove it from
            # the lobby invites_ids by the time we create the invite. This expiration
            # is just a data protection, that's why we multiply the time by 2, because if,
            # for some reason, the task doesn't remove it, we securely had it expired.
            pipe.expire(self.cache_key, LobbyInvite.Config.EXPIRE_TIME * 2)

        cache.protected_handler(transaction_operations, self.cache_key)
        return self

    def delete(self):
        def transaction_operations(pipe, _):
            pipe.delete(self.cache_key)

        cache.protected_handler(transaction_operations, self.cache_key)

        lobby = Lobby.get(self.lobby_id)
        lobby.invites_ids.remove(self.id)
        lobby.save()

    @staticmethod
    def incr_auto_id() -> int:
        return int(cache.incr(f'{LobbyInvite.Config.CACHE_PREFIX}:auto_id'))

    @staticmethod
    def create(lobby_id: int, from_player_id: int, to_player_id: int) -> LobbyInvite:
        lobby = Lobby.get_by_player_id(from_player_id, fail_silently=True)
        if not lobby:
            raise LobbyInviteException(
                _('Cannot invite players while in another lobby.')
            )

        exists = LobbyInvite.filter(lobby_id=lobby_id, to_player_id=to_player_id)
        if exists:
            raise LobbyInviteException(_('Invite already exists.'))

        auto_id = LobbyInvite.incr_auto_id()
        lobby.invites_ids.append(auto_id)
        lobby.save()
        invite = LobbyInvite(
            id=auto_id,
            lobby_id=lobby_id,
            from_player_id=from_player_id,
            to_player_id=to_player_id,
        )
        return invite.save()

    @staticmethod
    def get(id: int, fail_silently: bool = False):
        invite = cache.hgetall(f'{LobbyInvite.Config.CACHE_PREFIX}:{id}')
        if invite:
            return LobbyInvite(**invite)

        if not fail_silently:
            raise LobbyInviteException(_('Lobby invite not found'))

    @staticmethod
    def get_by_lobby_id(lobby_id: int):
        invite_list = []

        for key in cache.scan_keys(f'{LobbyInvite.Config.CACHE_PREFIX}:*'):
            if key.split(':')[-1].isdigit():
                model_hash = cache.hgetall(key)
                if int(model_hash.get('lobby_id', -1)) == lobby_id:
                    invite = LobbyInvite(**model_hash)
                    invite_list.append(invite)

        return invite_list

    @staticmethod
    def get_by_player_id(player_id: int, kind: str = 'all'):
        available_directions = ['sent', 'received', 'all']
        if kind not in available_directions:
            raise LobbyInviteException(
                _(f'Direction must be {(" or ").join(available_directions)}')
            )

        if kind == 'sent':
            return LobbyInvite.filter(from_player_id=player_id)
        elif kind == 'received':
            return LobbyInvite.filter(to_player_id=player_id)
        else:
            return LobbyInvite.filter(
                Q(to_player_id=player_id) | Q(from_player_id=player_id)
            )

        keys = cache.scan_keys(f'{LobbyInvite.Config.CACHE_PREFIX}:*')
        invite_list = []

        for key in keys:
            if key.split(':')[-1].isdigit():
                model_hash = cache.hgetall(key)
                from_id = int(model_hash.get('from_player_id', 0))
                to_id = int(model_hash.get('to_player_id', 0))

                if (
                    (direction == 'from' and from_id == player_id)
                    or (direction == 'to' and to_id == player_id)
                    or (
                        direction == 'both'
                        and (from_id == player_id or to_id == player_id)
                    )
                ):
                    invite = LobbyInvite(**model_hash)
                    invite_list.append(invite)

        return invite_list
