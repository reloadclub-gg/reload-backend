from __future__ import annotations

import random
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import RedisClient
from core.utils import str_to_timezone

from .invite import LobbyInvite
from .player import Player

cache = RedisClient()
User = get_user_model()


class LobbyException(Exception):
    pass


class Lobby(BaseModel):
    """
    This model represents the lobbies on Redis cache db.
    The Redis db keys from this model are described below:

    [key] __mm:lobby:[player_id] <current_lobby_id>
    [set] __mm:lobby:[player_id]:players <(player_id,...)>
    [key] __mm:lobby:[player_id]:is_public <0|1>
    [zset] __mm:lobby:[player_id]:invites <(from_player_id:to_player_id,...)>
    [key] __mm:lobby:[player_id]:queue <datetime>
    [key] __mm:lobby:[player_id]:type <competitive|custom>
    [key] __mm:lobby:[player_id]:mode <1|5|20>
    """

    owner_id: int

    class Config:
        CACHE_PREFIX: str = '__mm:lobby'
        TYPES: list = ['competitive', 'custom']
        MODES = {
            TYPES[0]: {'modes': [1, 5], 'default': 5},
            TYPES[1]: {'modes': [20], 'default': 20},
        }

    @property
    def cache_key(self):
        """
        The lobby key repr on Redis.
        """
        return f'{self.Config.CACHE_PREFIX}:{self.owner_id}'

    @property
    def id(self):
        """
        The lobby ID.
        """
        return self.owner_id

    @property
    def players_ids(self) -> list:
        """
        All player_ids that are in lobby. Owner included.
        """
        return sorted(list(map(int, cache.smembers(f'{self.cache_key}:players'))))

    @property
    def non_owners_ids(self) -> list:
        """
        All player_ids that are in lobby. Owner excluded.
        """
        return sorted([id for id in self.players_ids if id != self.owner_id])

    @property
    def is_public(self) -> bool:
        """
        Return wether lobby is public or private.
        Public (1) -> any online user, with a valid account can join.
        Private (0) -> only invited online users, with a valid account can join.
        """
        return cache.get(f'{self.cache_key}:public') == '1'

    @property
    def invites(self) -> list:
        """
        Retrieve all unaccepted invites.
        """
        invite_ids = sorted(list(cache.zrange(f'{self.cache_key}:invites', 0, -1)))
        return [
            LobbyInvite.get(lobby_id=self.id, invite_id=invite_id)
            for invite_id in invite_ids
        ]

    @property
    def invited_players_ids(self) -> list:
        """
        Retrieve all invited player_id's.
        """
        return sorted(list(map(int, [invite.to_id for invite in self.invites])))

    @property
    def queue(self) -> datetime:
        """
        Return wether the lobby is queued.
        """
        queue = cache.get(f'{self.cache_key}:queue')
        if queue:
            return str_to_timezone(queue)

    @property
    def queue_time(self) -> int:
        """
        Get how much time, in seconds, lobby is queued.
        """
        if self.queue:
            return (timezone.now() - self.queue).seconds

    @property
    def players_count(self) -> int:
        """
        Return how many players are in the lobby.
        """
        return len(self.players_ids)

    @property
    def seats(self) -> int:
        """
        Return how many seats are available for this lobby.
        """
        return self.max_players - self.players_count

    @property
    def overall(self) -> int:
        """
        The overall is the highest level among the players levels.
        """
        return max(
            list(
                User.objects.filter(id__in=self.players_ids).values_list(
                    'account__level', flat=True
                )
            )
            or [0]
        )

    @property
    def lobby_type(self) -> str:
        """
        Returns the lobby type which can be one of Config.TYPES.
        """
        return cache.get(f'{self.cache_key}:type')

    @property
    def mode(self) -> int:
        """
        Returns which competitive mode the lobby is on
        from Config.COMPETITIVE_MODES.
        """
        mode = cache.get(f'{self.cache_key}:mode')
        if mode:
            return int(mode)

    @property
    def max_players(self) -> int:
        """
        Returns how many players are allowed to take seat
        on this lobby. The returned value is the same return of
        the mode property.
        """
        return self.mode

    @property
    def restriction_countdown(self) -> int:
        """
        Return the greatest player restriction countdown in seconds.
        """
        lock_countdowns = [
            Player(user_id=player_id).lock_countdown
            for player_id in self.players_ids
            if Player(user_id=player_id).lock_countdown
        ]
        if lock_countdowns:
            return max(lock_countdowns)

    @staticmethod
    def is_owner(lobby_id: int, player_id: int) -> bool:
        lobby = Lobby(owner_id=lobby_id)

        return lobby.owner_id == player_id

    @staticmethod
    def delete(lobby_id: int, pipe=None):
        lobby = Lobby(owner_id=lobby_id)

        keys = cache.keys(f'{lobby.cache_key}:*')
        if len(keys) >= 1:
            if pipe:
                pipe.delete(*keys)
                pipe.delete(lobby.cache_key)
            else:
                cache.delete(*keys)
                cache.delete(lobby.cache_key)

    @staticmethod
    def cancel_all_queues():
        lobby_ids = [int(key.split(':')[2]) for key in cache.keys('__mm:lobby:*:queue')]
        for lobby_id in lobby_ids:
            lobby = Lobby(owner_id=lobby_id)
            lobby.cancel_queue()

    @staticmethod
    def get_current(player_id: int) -> Lobby:
        """
        Get the current lobby the user is.
        """
        lobby_id = cache.get(f'{Lobby.Config.CACHE_PREFIX}:{player_id}')
        if not lobby_id:
            return None
        return Lobby(owner_id=lobby_id)

    @staticmethod
    def create(owner_id: int, lobby_type: str = None, mode: int = None) -> Lobby:
        """
        Create a lobby for a given user.
        """
        filter = User.objects.filter(pk=owner_id)
        if not filter.exists():
            raise LobbyException(_('User not found.'))

        user = filter[0]
        if not hasattr(user, 'account') or not user.account.is_verified:
            raise LobbyException(
                _('A verified account is required to perform this action.')
            )

        if not user.is_online:
            raise LobbyException(_('Offline user.'))

        if lobby_type is not None and lobby_type not in Lobby.Config.TYPES:
            raise LobbyException(_('The given type is not valid.'))

        if not lobby_type:
            lobby_type = Lobby.Config.TYPES[0]

        if mode is not None and mode not in Lobby.Config.MODES[lobby_type].get('modes'):
            raise LobbyException(_('The given mode is not valid.'))

        if not mode:
            mode = Lobby.Config.MODES.get(lobby_type).get('default')

        lobby = Lobby(owner_id=owner_id)
        cache.set(lobby.cache_key, owner_id)
        cache.set(f'{lobby.cache_key}:type', lobby_type)
        cache.set(f'{lobby.cache_key}:mode', mode)
        cache.sadd(f'{lobby.cache_key}:players', owner_id)

        Player.create(user_id=owner_id)

        return lobby

    # flake8: noqa: C901
    @staticmethod
    def move(player_id: int, to_lobby_id: int, remove: bool = False) -> Lobby:
        """
        This method move players around between lobbies.
        If `to_lobby_id` == `player_id`, then this lobby
        should be empty, meaning that we need to remove every
        other player from it.

        If `remove` is True, it means that we need to purge this
        lobby, removing it from Redis cache. This usually happen
        when the owner logs out. Before lobby deletion, we move
        every other player (if there is any) to another lobby. We
        also need to cancel the queue for the current lobby.
        """

        from_lobby_id = cache.get(f'{Lobby.Config.CACHE_PREFIX}:{player_id}')
        from_lobby = Lobby(owner_id=from_lobby_id)
        to_lobby = Lobby(owner_id=to_lobby_id)

        def transaction_pre(pipe):
            if not pipe.get(from_lobby.cache_key) or not pipe.get(to_lobby.cache_key):
                raise LobbyException(_('Lobby not found.'))

        def transaction_operations(pipe, pre_result):
            filter = User.objects.filter(pk=player_id)
            new_lobby = None
            if not filter.exists():
                raise LobbyException(_('User not found.'))

            if not remove:
                joining_player = filter[0]
                if (
                    not hasattr(joining_player, 'account')
                    or not joining_player.account.is_verified
                ):
                    raise LobbyException(
                        _('A verified account is required to perform this action.')
                    )

                if not joining_player.is_online:
                    raise LobbyException(_('Offline user.'))

                if from_lobby.queue or to_lobby.queue:
                    raise LobbyException(_('Lobby is queued.'))

                is_owner = Lobby.is_owner(to_lobby_id, player_id)

                can_join = (
                    to_lobby.is_public
                    or player_id in to_lobby.invited_players_ids
                    or is_owner
                )

                if not to_lobby.seats and to_lobby.owner_id != player_id:
                    raise LobbyException(_('Lobby is full.'))

                if not can_join:
                    raise LobbyException(_('User must be invited.'))

            if from_lobby_id != to_lobby_id:
                pipe.srem(f'{from_lobby.cache_key}:players', player_id)
                pipe.sadd(f'{to_lobby.cache_key}:players', player_id)
                pipe.set(f'{Lobby.Config.CACHE_PREFIX}:{player_id}', to_lobby.owner_id)
                invite = to_lobby.get_invite_by_to_player_id(player_id)
                if invite:
                    pipe.zrem(f'{to_lobby.cache_key}:invites', invite.id)

            if len(from_lobby.non_owners_ids) > 0 and from_lobby.owner_id == player_id:
                new_owner_id = min(from_lobby.non_owners_ids)
                new_lobby = Lobby(owner_id=new_owner_id)

                pipe.srem(f'{from_lobby.cache_key}:players', *from_lobby.non_owners_ids)

                # If another instance tries to move a player to the new_lobby,
                # a transaction will start there and when we add a player here
                # in the following line, the other transaction will fail and
                # try again/rollback.
                pipe.sadd(f'{new_lobby.cache_key}:players', *from_lobby.non_owners_ids)

                for other_player_id in from_lobby.non_owners_ids:
                    pipe.set(
                        f'{Lobby.Config.CACHE_PREFIX}:{other_player_id}',
                        new_lobby.owner_id,
                    )
                    invite = new_lobby.get_invite_by_to_player_id(other_player_id)
                    if invite:
                        pipe.zrem(f'{new_lobby.cache_key}:invites', invite)

            if remove:
                Lobby.delete(to_lobby.id, pipe=pipe)
                from_lobby.cancel_queue()
                invites_to_player = LobbyInvite.get_by_to_user_id(player_id)
                for invite in invites_to_player:
                    pipe.zrem(f'__mm:lobby:{invite.lobby_id}:invites', invite.id)

                Player.delete(player_id)

            return new_lobby

        return cache.protected_handler(
            transaction_operations,
            f'{from_lobby.cache_key}:players',
            f'{from_lobby.cache_key}:queue',
            f'{to_lobby.cache_key}:players',
            f'{to_lobby.cache_key}:queue',
            f'{Lobby.Config.CACHE_PREFIX}:{player_id}',
            f'{to_lobby.cache_key}:invites',
            pre_func=transaction_pre,
            value_from_callable=True,
        )

    @staticmethod
    def get_all_queued():
        queued_ids = [
            int(key.split(':')[2]) for key in cache.keys('__mm:lobby:*:queue')
        ]
        return [Lobby(owner_id=queued_id) for queued_id in queued_ids]

    def invite(self, from_player_id: int, to_player_id: int) -> LobbyInvite:
        """
        Lobby players can invite others players to join them in the lobby following
        these rules:
        - Lobby should not be full;
        - Player should not been invited yet;
        - Invited user should exist, be online and have a verified account;
        """

        if not self.seats:
            raise LobbyException(_('Lobby is full.'))

        if self.queue:
            raise LobbyException(_('Lobby is queued.'))

        def transaction_pre(pipe):
            can_invite = pipe.sismember(f'{self.cache_key}:players', from_player_id)
            already_player = pipe.sismember(f'{self.cache_key}:players', to_player_id)
            already_invited = to_player_id in self.invited_players_ids
            return (can_invite, already_player, already_invited)

        def transaction_operations(pipe, pre_result):
            can_invite, already_player, already_invited = pre_result

            if not can_invite:
                raise LobbyException(
                    'Usuário não tem permissão para realizar essa ação.'
                )

            if already_player:
                raise LobbyException(_('Invited user is already a lobby player.'))

            if already_invited:
                raise LobbyException(_('User already invited.'))

            filter = User.objects.filter(pk=to_player_id)
            if not filter.exists():
                raise LobbyException(_('User not found.'))

            invited = filter[0]
            if not hasattr(invited, 'account') or not invited.account.is_verified:
                raise LobbyException(
                    _('A verified account is required to perform this action.')
                )

            if not invited.is_online:
                raise LobbyException(_('Offline user.'))

            pipe.zadd(
                f'{self.cache_key}:invites',
                {f'{from_player_id}:{to_player_id}': timezone.now().timestamp()},
            )

        cache.protected_handler(
            transaction_operations,
            f'{self.cache_key}:players',
            f'{self.cache_key}:queue',
            f'{self.cache_key}:invites',
            pre_func=transaction_pre,
        )

        return LobbyInvite(
            from_id=from_player_id, to_id=to_player_id, lobby_id=self.owner_id
        )

    def get_invite_by_to_player_id(self, to_player_id: int) -> str:
        result = None
        for invite in self.invites:
            if to_player_id == invite.to_id:
                result = invite

        return result

    def get_invites_by_from_player_id(self, from_player_id: int) -> str:
        return [invite for invite in self.invites if from_player_id == invite.from_id]

    def delete_invite(self, invite_id):
        """
        Method to delete an existing invite
        Invite should exist on lobby invites list
        Should return False if the requested invite_id isn't in the lobby invites list
        """
        invite = cache.zscore(f'{self.cache_key}:invites', invite_id)

        if not invite:
            raise LobbyException(_('Invite not found.'))

        def transaction_operations(pipe, pre_result):
            pipe.zrem(f'{self.cache_key}:invites', invite_id)

        cache.protected_handler(transaction_operations, f'{self.cache_key}:invites')

    def start_queue(self):
        """
        Add lobby to the queue.
        """
        if self.queue:
            raise LobbyException(_('Lobby is queued.'))

        for user_id in self.players_ids:
            if Player.get_by_user_id(user_id=user_id).lock_date:
                raise LobbyException(_('Can\'t start queue due to player restriction.'))

        def transaction_operations(pipe, pre_result):
            pipe.set(f'{self.cache_key}:queue', timezone.now().isoformat())

        cache.protected_handler(
            transaction_operations,
            f'{self.cache_key}:players',
            f'{self.cache_key}:queue',
            f'{self.cache_key}:invites',
        )

    def cancel_queue(self):
        """
        Remove lobby from queue.
        """
        cache.delete(f'{self.cache_key}:queue')

    def set_public(self):
        """
        Change lobby privacy to public.
        """
        if self.queue:
            raise LobbyException(_('Lobby is queued.'))

        cache.set(f'{self.cache_key}:public', 1)

    def set_private(self):
        """
        Change lobby privacy to private.
        """
        if self.queue:
            raise LobbyException(_('Lobby is queued.'))

        cache.set(f'{self.cache_key}:public', 0)

    def set_type(self, lobby_type: str):
        """
        Sets the lobby type, which can be any value from Config.TYPES.
        If no type is received or type isn't on Config.TYPES,
        then defaults to Config.TYPES[0].
        """
        if self.queue:
            raise LobbyException(_('Lobby is queued.'))

        if lobby_type not in self.Config.TYPES:
            raise LobbyException(_('The given type is not valid.'))

        cache.set(f'{self.cache_key}:type', lobby_type)

    def set_mode(self, mode, players_id_to_remove=[]):
        """
        Sets the lobby mode, which can be any value from Config.MODES.
        If no mode is received or type isn't on Config.MODES,
        then defaults to Config.COMP_DEFAULT_MODE.
        """
        if self.queue:
            raise LobbyException(_('Lobby is queued.'))

        if mode not in self.Config.MODES[self.lobby_type].get('modes'):
            raise LobbyException(_('The given mode is not valid.'))

        players_ids = self.non_owners_ids

        if self.players_count > mode:
            if self.owner_id in players_id_to_remove:
                raise LobbyException(_('Owner cannot be removed.'))
            elif not players_id_to_remove:
                for i in range(self.players_count - mode):
                    choice = random.choice(players_ids)
                    players_ids.remove(choice)
                    self.move(choice, choice)
            else:
                for player_id in players_id_to_remove:
                    players_ids.remove(player_id)
                    self.move(player_id, player_id)

        cache.set(f'{self.cache_key}:mode', mode)

    def get_min_max_overall_by_queue_time(self) -> tuple:
        """
        Return the minimum and maximum lobby overall that this lobby
        can team up or challenge.
        """
        elapsed_time = int(self.queue_time)

        if not self.queue or elapsed_time < 30:
            min = self.overall - 1 if self.overall > 0 else 0
            max = self.overall + 1
        elif elapsed_time < 60:
            min = self.overall - 2 if self.overall > 1 else 0
            max = self.overall + 2
        elif elapsed_time < 90:
            min = self.overall - 3 if self.overall > 2 else 0
            max = self.overall + 3
        elif elapsed_time < 120:
            min = self.overall - 4 if self.overall > 3 else 0
            max = self.overall + 4
        else:
            min = self.overall - 5 if self.overall > 4 else 0
            max = self.overall + 5

        return min, max
