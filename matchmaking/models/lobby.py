from __future__ import annotations
import random
from datetime import datetime

from pydantic import BaseModel

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.utils import str_to_timezone
from core.redis import RedisClient
from .invite import LobbyInvite

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
    [set] __mm:lobby:[player_id]:invites <(from_player_id:to_player_id,...)>
    [key] __mm:lobby:[player_id]:queue <datetime>
    [key] __mm:lobby:[player_id]:type <competitive|custom>
    [key] __mm:lobby:[player_id]:mode <1|5|20>
    """

    class Config:
        CACHE_PREFIX: str = '__mm:lobby'
        TYPES: list = ['competitive', 'custom']
        MODES = {
            TYPES[0]: {'modes': [1, 5], 'default': 5},
            TYPES[1]: {'modes': [20], 'default': 20},
        }

    owner_id: int

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
        return list(map(int, cache.smembers(f'{self.cache_key}:players')))

    @property
    def non_owners_ids(self) -> list:
        """
        All player_ids that are in lobby. Owner excluded.
        """
        return [id for id in self.players_ids if id != self.owner_id]

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
        return list(cache.smembers(f'{self.cache_key}:invites'))

    @property
    def invited_players_ids(self) -> list:
        """
        Retrieve all invited player_id's.
        """
        return list(map(int, [invite.split(':')[1] for invite in self.invites]))

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
            [
                user.account.level
                for user in User.objects.filter(id__in=self.players_ids)
            ]
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
        return int(cache.get(f'{self.cache_key}:mode'))

    @property
    def max_players(self) -> int:
        """
        Returns how many players are allowed to take seat
        on this lobby. The returned value is the same return of
        the mode property.
        """
        return self.mode

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
            raise LobbyException('User not found caught on lobby creation')

        user = filter[0]
        if not hasattr(user, 'account') or not user.account.is_verified:
            raise LobbyException(
                'User don\'t have a verified account caught on lobby creation'
            )

        if not user.is_online:
            raise LobbyException('Offline user caught on lobby creation')

        if lobby_type is not None and lobby_type not in Lobby.Config.TYPES:
            avail_types = ','.join(Lobby.Config.TYPES)
            raise LobbyException(
                f'Type unknown, should be one of the following: {avail_types}'
            )

        if not lobby_type:
            lobby_type = Lobby.Config.TYPES[0]

        if mode is not None and mode not in Lobby.Config.MODES[lobby_type].get('modes'):
            avail_modes = ','.join(
                str(x) for x in Lobby.Config.MODES.get(lobby_type).get('modes')
            )
            raise LobbyException(
                f'Mode unknown, should be one of the following: {avail_modes}'
            )

        if not mode:
            mode = Lobby.Config.MODES.get(lobby_type).get('default')

        lobby = Lobby(owner_id=owner_id)
        cache.set(lobby.cache_key, owner_id)
        cache.set(f'{lobby.cache_key}:type', lobby_type)
        cache.set(f'{lobby.cache_key}:mode', mode)
        cache.sadd(f'{lobby.cache_key}:players', owner_id)

        return lobby

    # flake8: noqa: C901
    @staticmethod
    def move(player_id: int, to_lobby_id: int, remove: bool = False):
        """
        This method move players around between lobbies.
        If `to_lobby_id` == `player_id`, then this lobby
        should be empty, meaning that we need to remove every
        other player from it.

        If `remove` is True, it means that we need to purge this
        lobby, removing it from Redis cache. This usually happen
        when the owner logs out. Before lobby deletion, we move
        every other player (if there is any) to another lobby.
        """

        from_lobby_id = cache.get(f'{Lobby.Config.CACHE_PREFIX}:{player_id}')
        from_lobby = Lobby(owner_id=from_lobby_id)
        to_lobby = Lobby(owner_id=to_lobby_id)

        def transaction_pre(pipe):
            if not pipe.get(from_lobby.cache_key) or not pipe.get(to_lobby.cache_key):
                raise LobbyException('Lobby not found caught on lobby move')

        def transaction_operations(pipe, _):
            filter = User.objects.filter(pk=player_id)
            if not filter.exists():
                raise LobbyException('User not found caught on lobby move')

            if not remove:
                joining_player = filter[0]
                if (
                    not hasattr(joining_player, 'account')
                    or not joining_player.account.is_verified
                ):
                    raise LobbyException(
                        'User don\'t have a verified account caught on lobby move'
                    )

                if not joining_player.is_online:
                    raise LobbyException('Offline user caught on lobby move')

                if from_lobby.queue or to_lobby.queue:
                    raise LobbyException('Lobby is queued caught on lobby move')

                is_owner = to_lobby.owner_id == player_id
                can_join = (
                    to_lobby.is_public
                    or player_id in to_lobby.invited_players_ids
                    or is_owner
                )

                if not to_lobby.seats:
                    raise LobbyException('Lobby is full caught on lobby move')

                if not can_join:
                    raise LobbyException('User not invited caught on lobby move')

            if from_lobby_id != to_lobby_id:
                pipe.srem(f'{from_lobby.cache_key}:players', player_id)
                pipe.sadd(f'{to_lobby.cache_key}:players', player_id)
                pipe.set(f'{Lobby.Config.CACHE_PREFIX}:{player_id}', to_lobby.owner_id)
                invite = to_lobby.get_invite_by_to_player_id(player_id)
                if invite:
                    pipe.srem(f'{to_lobby.cache_key}:invites', invite)

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
                        pipe.srem(f'{new_lobby.cache_key}:invites', invite)

            invites_from_player = from_lobby.get_invites_by_from_player_id(player_id)
            for invite in invites_from_player:
                from_lobby.delete_invite(invite)

            if remove:
                pipe.delete(to_lobby.cache_key)
                pipe.delete(f'{to_lobby.cache_key}:players')
                pipe.delete(f'{to_lobby.cache_key}:queue')
                pipe.delete(f'{to_lobby.cache_key}:is_public')
                pipe.delete(f'{to_lobby.cache_key}:invites')

        cache.protected_handler(
            transaction_operations,
            f'{from_lobby.cache_key}:players',
            f'{from_lobby.cache_key}:queue',
            f'{to_lobby.cache_key}:players',
            f'{to_lobby.cache_key}:queue',
            f'{Lobby.Config.CACHE_PREFIX}:{player_id}',
            f'{to_lobby.cache_key}:invites',
            pre_func=transaction_pre,
        )

    def invite(self, from_player_id: int, to_player_id: int) -> LobbyInvite:
        """
        Lobby players can invite others players to join them in the lobby following
        these rules:
        - Lobby should not be full;
        - Player should not been invited yet;
        - Invited user should exist, be online and have a verified account;
        """

        if not self.seats:
            raise LobbyException('Lobby is full caught on lobby invite')

        if self.queue:
            raise LobbyException('Lobby is queued caught on lobby invite')

        def transaction_pre(pipe):
            can_invite = pipe.sismember(f'{self.cache_key}:players', from_player_id)
            already_player = pipe.sismember(f'{self.cache_key}:players', to_player_id)
            already_invited = to_player_id in self.invited_players_ids
            return (can_invite, already_player, already_invited)

        def transaction_operations(pipe, pre_result):

            can_invite, already_player, already_invited = pre_result

            if not can_invite:
                raise LobbyException('User cannot invite caught on lobby invite')

            if already_player:
                raise LobbyException('User already on lobby caught on lobby invite')

            if already_invited:
                raise LobbyException('User already invited caught on lobby invite')

            filter = User.objects.filter(pk=to_player_id)
            if not filter.exists():
                raise LobbyException('User not found caught on lobby invite')

            invited = filter[0]
            if not hasattr(invited, 'account') or not invited.account.is_verified:
                raise LobbyException(
                    'User don\'t have a verified account caught on lobby invite'
                )

            if not invited.is_online:
                raise LobbyException('Offline user caught on lobby invite')

            pipe.sadd(f'{self.cache_key}:invites', f'{from_player_id}:{to_player_id}')

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
        for invite_id in self.invites:
            if to_player_id == int(invite_id.split(':')[1]):
                result = invite_id

        return result

    def get_invites_by_from_player_id(self, from_player_id: int) -> str:
        return [
            invite
            for invite in self.invites
            if from_player_id == int(invite.split(':')[0])
        ]

    def delete_invite(self, invite_id):
        """
        Method to delete an existing invite
        Invite should exist on lobby invites list
        Should return False if the requested invite_id isn't in the lobby invites list
        """
        invite = cache.sismember(f'{self.cache_key}:invites', invite_id)

        if not invite:
            raise LobbyException('Inexistent invite caught on invite deletion')

        def transaction_operations(pipe, _):
            pipe.srem(f'{self.cache_key}:invites', invite_id)

        cache.protected_handler(transaction_operations, f'{self.cache_key}:invites')

    def start_queue(self):
        """
        Add lobby to the queue.
        """
        if self.queue:
            raise LobbyException('Lobby is queued caught on start lobby queue')

        def transaction_operations(pipe, _):
            pipe.set(f'{self.cache_key}:queue', timezone.now().isoformat())
            pipe.delete(f'{self.cache_key}:invites')

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
            raise LobbyException('Lobby is queued caught on set lobby public')

        cache.set(f'{self.cache_key}:public', 1)

    def set_private(self):
        """
        Change lobby privacy to private.
        """
        if self.queue:
            raise LobbyException('Lobby is queued caught on set lobby private')

        cache.set(f'{self.cache_key}:public', 0)

    def set_type(self, lobby_type: str):
        """
        Sets the lobby type, which can be any value from Config.TYPES.
        If no type is received or type isn't on Config.TYPES,
        then defaults to Config.TYPES[0].
        """
        if self.queue:
            raise LobbyException('Lobby is queued caught on set lobby type')

        if lobby_type not in self.Config.TYPES:
            avail_types = ','.join(Lobby.Config.TYPES)
            raise LobbyException(
                f'Type unknown, should be one of the following: {avail_types}'
            )

        cache.set(f'{self.cache_key}:type', lobby_type)

    def set_mode(self, mode, players_id_to_remove=[]):
        """
        Sets the lobby mode, which can be any value from Config.MODES.
        If no mode is received or type isn't on Config.MODES,
        then defaults to Config.COMP_DEFAULT_MODE.
        """
        if self.queue:
            raise LobbyException('Lobby is queued caught on set lobby mode')

        if mode not in self.Config.MODES[self.lobby_type].get('modes'):
            avail_modes = ','.join(
                str(x) for x in Lobby.Config.MODES.get(self.lobby_type).get('modes')
            )

            raise LobbyException(
                f'Mode unknown, should be one of the following: {avail_modes}'
            )

        players_ids = self.non_owners_ids

        if self.players_count > mode:
            if self.owner_id in players_id_to_remove:
                raise LobbyException('owner_id cannot be removed')
            elif not players_id_to_remove:
                for _ in range(self.players_count - mode):
                    choice = random.choice(players_ids)
                    players_ids.remove(choice)
                    self.move(choice, choice)
            else:
                for player_id in players_id_to_remove:
                    players_ids.remove(player_id)
                    self.move(player_id, player_id)

        cache.set(f'{self.cache_key}:mode', mode)
