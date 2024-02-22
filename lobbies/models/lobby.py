from __future__ import annotations

import logging
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import TextChoices
from django.utils import timezone
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import redis_client_instance as cache
from core.utils import str_to_timezone
from matches.models import Map

from .invite import LobbyInvite
from .player import PlayerRestriction

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
    [key] __mm:lobby:[player_id]:mode <competitive|custom>
    [key] __mm:lobby:[player_id]:match_type <default|deathmatch|safezone>
    [set] __mm:lobby:[player_id]:def_players_ids <(player_id,...)>
    [set] __mm:lobby:[player_id]:atk_players_ids <(player_id,...)>
    [set] __mm:lobby:[player_id]:spec_players_ids <(player_id,...)>
    [set] __mm:lobby:[player_id]:map_id <map_id>
    [set] __mm:lobby:[player_id]:weapon <weapon_id>
    """

    owner_id: int

    class Config:
        CACHE_PREFIX: str = '__mm:lobby'
        MAX_SEATS: dict = {
            'competitive': 5,
            'custom': 15,  # 10 players + 5 specs
        }
        MAPS: dict = {'default': [1, 2, 3, 4], 'safezone': [5, 6, 7]}

    class ModeChoices(TextChoices):
        COMP = 'competitive'
        CUSTOM = 'custom'

    class TypeChoices(TextChoices):
        DEFAULT = 'default'
        SAFEZONE = 'safezone'

    class WeaponChoices(TextChoices):
        WEAPON_APPISTOL = 'Rapidinha'
        WEAPON_ASSAULTRIFLE = 'AK'
        WEAPON_ASSAULTSHOTGUN = 'Bull'
        WEAPON_COMBATMG = 'Rambão'
        WEAPON_HEAVYSNIPER = 'Sniper'
        WEAPON_MG = 'Rambinho'
        WEAPON_MICROSMG = 'Micro'
        WEAPON_PISTOL = 'Pistola'
        WEAPON_PISTOL50 = 'Trinta e Oito'
        WEAPON_PISTOL_MK2 = '9idade'
        WEAPON_PUMPSHOTGUN = 'Doze'
        WEAPON_SMG = 'Nova'
        WEAPON_SNIPERRIFLE = 'Teco-Teco'
        WEAPON_TACTICALRIFLE = 'M4'
        WEAPON_KNIFE = 'Faca'

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
    def mode(self) -> int:
        """
        Returns if the lobby is competitive or a custom game.
        """
        return cache.get(f'{self.cache_key}:mode')

    @property
    def max_players(self) -> int:
        """
        Returns how many players are allowed to take seat
        on this lobby.
        """
        return Lobby.Config.MAX_SEATS.get(self.mode)

    @property
    def weapon(self) -> str:
        """
        Returns the lobby match type.
        """
        return cache.get(f'{self.cache_key}:weapon')

    @property
    def def_players_ids(self) -> str:
        """
        Returns the lobby atk players (for custom mode).
        """
        return sorted(
            list(map(int, cache.smembers(f'{self.cache_key}:def_players_ids')))
        )

    @property
    def atk_players_ids(self) -> str:
        """
        Returns the lobby def players (for custom mode).
        """
        return sorted(
            list(map(int, cache.smembers(f'{self.cache_key}:atk_players_ids')))
        )

    @property
    def spec_players_ids(self) -> str:
        """
        Returns the lobby spec players (for custom mode).
        """
        return sorted(
            list(map(int, cache.smembers(f'{self.cache_key}:spec_players_ids')))
        )

    @property
    def map_id(self) -> int:
        """
        Returns the lobby map_id (for custom mode).
        """
        map_id = cache.get(f'{self.cache_key}:map_id')
        if map_id:
            return int(map_id)

    @property
    def match_type(self) -> str:
        """
        Returns the type of a match from the custom lobby.
        """
        return cache.get(f'{self.cache_key}:match_type')

    @property
    def restriction_countdown(self) -> int:
        """
        Return the greatest player restriction countdown in seconds.
        """
        restriction_end_dates = PlayerRestriction.objects.filter(
            user_id__in=self.players_ids,
            end_date__gte=timezone.now(),
        ).values_list('end_date', flat=True)
        restriction_countdowns = [
            (date - timezone.now()).seconds for date in restriction_end_dates
        ]

        if restriction_countdowns:
            return max(restriction_countdowns)

    @staticmethod
    def is_owner(lobby_id: int, player_id: int) -> bool:
        lobby = Lobby(owner_id=lobby_id)

        return lobby.owner_id == player_id

    @staticmethod
    def delete(lobby_id: int, pipe=None):
        lobby = Lobby(owner_id=lobby_id)
        keys = list(cache.scan_keys(f'{lobby.cache_key}:*'))
        if keys:
            if pipe:
                pipe.delete(*keys)
                pipe.delete(lobby.cache_key)
            else:
                cache.delete(*keys)
                cache.delete(lobby.cache_key)

    @staticmethod
    def cancel_all_queues():
        keys = list(cache.scan_keys('__mm:lobby:*:queue'))
        if not keys:
            return

        lobby_ids = [int(key.split(':')[2]) for key in keys]

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
    def create(owner_id: int) -> Lobby:
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

        lobby = Lobby(owner_id=owner_id)
        cache.set(lobby.cache_key, owner_id)
        cache.set(f'{lobby.cache_key}:mode', Lobby.ModeChoices.COMP)
        cache.sadd(f'{lobby.cache_key}:players', owner_id)
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

        logging.info('')
        logging.info('-- lobby_move start --')
        logging.info('')

        logging.info(f'[lobby_move] player_id {player_id}')
        logging.info(f'[lobby_move] to_lobby_id {to_lobby_id}')
        logging.info(f'[lobby_move] remove {remove}')

        from_lobby_id = cache.get(f'{Lobby.Config.CACHE_PREFIX}:{player_id}')
        if not from_lobby_id:
            raise LobbyException(_('There is no lobby to move user from.'))

        logging.info(f'[lobby_move] from_lobby_id {from_lobby_id}')

        from_lobby = Lobby(owner_id=from_lobby_id)
        to_lobby = Lobby(owner_id=to_lobby_id)

        logging.info(f'[lobby_move] from_lobby {from_lobby}')
        logging.info(f'[lobby_move] to_lobby {to_lobby}')

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

                logging.info(f'[lobby_move] is_owner {is_owner}')
                logging.info(f'[lobby_move] can_join {can_join}')

                if not to_lobby.seats and to_lobby.owner_id != player_id:
                    raise LobbyException(_('Lobby is full.'))

                if not can_join:
                    raise LobbyException(_('User must be invited.'))

            if from_lobby_id != to_lobby_id:
                pipe.srem(f'{from_lobby.cache_key}:players', player_id)
                logging.info(f'[lobby_move] removed {player_id} from {from_lobby.id}')
                pipe.sadd(f'{to_lobby.cache_key}:players', player_id)
                logging.info(f'[lobby_move] added {player_id} to {to_lobby.id}')
                pipe.set(f'{Lobby.Config.CACHE_PREFIX}:{player_id}', to_lobby.owner_id)
                logging.info(
                    f'[lobby_move] update player lobby: {player_id} - {to_lobby.owner_id}'
                )
                invite = to_lobby.get_invite_by_to_player_id(player_id)
                if invite:
                    logging.info(f'[lobby_move] invite: {invite.id}')
                    pipe.zrem(f'{to_lobby.cache_key}:invites', invite.id)

                if to_lobby.mode == Lobby.ModeChoices.CUSTOM:
                    to_lobby.__move_player_to_custom_side(player_id)

            if len(from_lobby.non_owners_ids) > 0 and from_lobby.owner_id == player_id:
                new_owner_id = min(from_lobby.non_owners_ids)
                logging.info(f'[lobby_move] new owner: {new_owner_id}')
                new_lobby = Lobby(owner_id=new_owner_id)
                logging.info(f'[lobby_move] new_lobby: {new_lobby.id}')

                pipe.srem(f'{from_lobby.cache_key}:players', *from_lobby.non_owners_ids)
                logging.info(
                    f'[lobby_move] remove from lobby: {from_lobby.id} -> {from_lobby.non_owners_ids}'
                )

                # If another instance tries to move a player to the new_lobby,
                # a transaction will start there and when we add a player here
                # in the following line, the other transaction will fail and
                # try again/rollback.
                pipe.sadd(f'{new_lobby.cache_key}:players', *from_lobby.non_owners_ids)
                logging.info(
                    f'[lobby_move] add to lobby: {new_lobby.id} -> {from_lobby.non_owners_ids}'
                )

                logging.info(f'[lobby_move] new_lobby: {new_lobby.id}')

                for other_player_id in from_lobby.non_owners_ids:
                    pipe.set(
                        f'{Lobby.Config.CACHE_PREFIX}:{other_player_id}',
                        new_lobby.owner_id,
                    )
                    logging.info(
                        f'[lobby_move] update player lobby: {other_player_id} - {new_lobby.owner_id}'
                    )
                    invite = new_lobby.get_invite_by_to_player_id(other_player_id)
                    if invite:
                        logging.info(f'[lobby_move] invite: {invite.id}')
                        pipe.zrem(f'{new_lobby.cache_key}:invites', invite)

            if remove:
                logging.info('[lobby_move] lobby deletion')
                Lobby.delete(to_lobby.id, pipe=pipe)
                from_lobby.cancel_queue()
                invites_to_player = LobbyInvite.get_by_to_user_id(player_id)
                logging.info(f'[lobby_move] invites {invites_to_player}')
                for invite in invites_to_player:
                    pipe.zrem(f'__mm:lobby:{invite.lobby_id}:invites', invite.id)

            logging.info('')
            logging.info('-- lobby_move end --')
            logging.info('')
            return new_lobby

        remnant_lobby = cache.protected_handler(
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
        logging.info(f'[lobby_move] remnant lobby: {remnant_lobby}')

        if to_lobby.players_count > 1:
            status = User.Status.TEAMING
        else:
            status = User.Status.ONLINE
        User.objects.filter(id__in=to_lobby.players_ids).update(status=status)
        if to_lobby.players_ids:
            logging.info(f'[lobby_move] to_lobby: {to_lobby.players_ids} -> {status}')

        if from_lobby.players_count <= 1:
            User.objects.filter(id__in=from_lobby.players_ids).update(
                status=User.Status.ONLINE
            )
            if from_lobby.players_count > 0:
                logging.info(
                    f'[lobby_move] from_lobby: {from_lobby.players_ids} -> online'
                )

        if remnant_lobby:
            if remnant_lobby.players_count <= 1:
                User.objects.filter(id__in=remnant_lobby.players_ids).update(
                    status=User.Status.ONLINE
                )
                if remnant_lobby.players_count > 0:
                    logging.info(
                        f'[lobby_move] remnant_lobby: {remnant_lobby.players_ids} -> online'
                    )

        return remnant_lobby

    @staticmethod
    def get_all_queued():
        keys = list(cache.scan_keys('__mm:lobby:*:queue'))
        if not keys:
            return []

        queued_ids = [int(key.split(':')[2]) for key in keys]
        queued_lobbies = [Lobby(owner_id=queued_id) for queued_id in queued_ids]
        free_lobbies = []
        for lobby in queued_lobbies:
            players = User.objects.filter(id__in=lobby.players_ids)
            if all(
                [
                    not player.account.pre_match and player.account.get_match() is None
                    for player in players
                ]
            ):
                free_lobbies.append(lobby)

        return free_lobbies

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
            from_id=from_player_id,
            to_id=to_player_id,
            lobby_id=self.owner_id,
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

        if self.mode == Lobby.ModeChoices.CUSTOM:
            raise LobbyException(_('Lobby can\'t be queued in this mode.'))

        if self.restriction_countdown:
            raise LobbyException(_('Can\'t start queue due to player restriction.'))

        def transaction_operations(pipe, pre_result):
            pipe.set(f'{self.cache_key}:queue', timezone.now().isoformat())

        cache.protected_handler(
            transaction_operations,
            f'{self.cache_key}:players',
            f'{self.cache_key}:queue',
            f'{self.cache_key}:invites',
        )

        User.objects.filter(id__in=self.players_ids).update(status=User.Status.QUEUED)

    def cancel_queue(self):
        """
        Remove lobby from queue.
        """
        cache.delete(f'{self.cache_key}:queue')
        if self.players_count > 1:
            User.objects.filter(id__in=self.players_ids).update(
                status=User.Status.TEAMING
            )
        else:
            User.objects.filter(id__in=self.players_ids).update(
                status=User.Status.ONLINE
            )

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

    def __move_comp_players_to_custom_sides(self):
        sides = ['def_players_ids', 'atk_players_ids', 'spec_players_ids']
        side_max_seats = int(
            Lobby.Config.MAX_SEATS.get(Lobby.ModeChoices.CUSTOM) / len(sides)
        )
        unsided_players = list(
            set(self.players_ids)
            - set(self.def_players_ids)
            - set(self.atk_players_ids)
            - set(self.spec_players_ids)
        )

        for player_id in unsided_players:
            for side in sides:
                side_list = getattr(self, side)
                if len(side_list) < side_max_seats:
                    cache.sadd(f'{self.cache_key}:{side}', player_id)
                    break

    def __move_player_to_custom_side(self, player_id: int):
        sides = ['def_players_ids', 'atk_players_ids', 'spec_players_ids']
        side_max_seats = int(
            Lobby.Config.MAX_SEATS.get(Lobby.ModeChoices.CUSTOM) / len(sides)
        )
        for side in sides:
            side_list = getattr(self, side)
            if len(side_list) < side_max_seats:
                cache.sadd(f'{self.cache_key}:{side}', player_id)
                break

    def __reset_to_comp_mode(self):
        pipe = cache.pipeline()
        for key in [
            'match_type',
            'map_id',
            'def_players_ids',
            'atk_players_ids',
            'spec_players_ids',
            'weapon',
        ]:
            pipe.delete(f'{self.cache_key}:{key}')
        pipe.execute()

    def __change_mode_checks(self, mode: str):
        if self.queue:
            raise LobbyException(_('Lobby is queued.'))

        if mode not in Lobby.ModeChoices.__members__.values():
            raise LobbyException(_('The given mode is not valid.'))

        if mode == self.mode:
            raise LobbyException(_('Mode already set.'))

        if mode == Lobby.ModeChoices.COMP and len(
            self.players_ids
        ) > Lobby.Config.MAX_SEATS.get(Lobby.ModeChoices.COMP):
            raise LobbyException(_('Cannot change mode of a oversized lobby.'))

    def set_mode(self, mode: str):
        """
        Sets the lobby mode.
        """
        self.__change_mode_checks(mode)

        if mode == Lobby.ModeChoices.CUSTOM:
            self.__move_comp_players_to_custom_sides()
            cache.set(f'{self.cache_key}:match_type', Map.MapTypeChoices.DEFAULT)
            cache.set(
                f'{self.cache_key}:map_id',
                Map.objects.filter(map_type=self.match_type)
                .values_list(
                    'id',
                    flat=True,
                )
                .first(),
            )
        else:
            self.__reset_to_comp_mode()

        cache.set(f'{self.cache_key}:mode', mode)

    def set_match_type(self, match_type: str):
        """
        Sets the lobby match type for custom lobbies.
        """
        if self.mode != Lobby.ModeChoices.CUSTOM:
            raise LobbyException(_('Cannot change type in this mode.'))

        if self.queue:
            raise LobbyException(_('Lobby is queued.'))

        if match_type not in Map.MapTypeChoices.__members__.values():
            raise LobbyException(_('The given type is not valid.'))

        cache.set(f'{self.cache_key}:match_type', match_type)
        cache.set(
            f'{self.cache_key}:map_id',
            Map.objects.filter(map_type=match_type)
            .values_list(
                'id',
                flat=True,
            )
            .first(),
        )

    def set_map_id(self, map_id: int):
        if self.mode != Lobby.ModeChoices.CUSTOM:
            raise LobbyException(_('Cannot restrict map in this mode.'))

        available_map_ids = Map.objects.filter(map_type=self.match_type).values_list(
            'id',
            flat=True,
        )
        if map_id not in available_map_ids:
            raise LobbyException(_('Invalid map id.'))
        cache.set(f'{self.cache_key}:map_id', map_id)

    def set_weapon(self, weapon: str = 'all'):
        if self.mode != Lobby.ModeChoices.CUSTOM:
            raise LobbyException(_('Cannot restrict weapon in this mode.'))

        if weapon == 'all':
            cache.delete(f'{self.cache_key}:weapon')
        elif weapon and weapon not in Lobby.WeaponChoices.__members__.values():
            raise LobbyException(_('Invalid weapon.'))
        else:
            cache.set(f'{self.cache_key}:weapon', weapon)

    def change_player_side(self, player_id: int, side: str):
        if self.mode != Lobby.ModeChoices.CUSTOM:
            raise LobbyException(_('Cannot change side in this mode.'))

        if player_id not in self.players_ids:
            raise LobbyException(_('Player not found.'))

        available_sides = ['atk_players_ids', 'def_players_ids', 'spec_players_ids']
        if side not in available_sides:
            raise LobbyException(_('Invalid side.'))

        side_max_seats = int(self.max_players / len(available_sides))
        if len(getattr(self, side)) >= side_max_seats:
            raise LobbyException(_('Side is full.'))

        if player_id in getattr(self, side):
            raise LobbyException(_('Player already on side.'))

        available_sides.remove(side)
        player_side = (
            available_sides[0]
            if player_id in getattr(self, available_sides[0])
            else available_sides[1]
        )

        cache.srem(f'{self.cache_key}:{player_side}', player_id)
        cache.sadd(f'{self.cache_key}:{side}', player_id)

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
