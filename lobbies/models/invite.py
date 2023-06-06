from __future__ import annotations

from typing import List

from django.utils import timezone
from django.utils.translation import gettext as _
from pydantic import BaseModel

from core.redis import RedisClient

cache = RedisClient()


class LobbyInviteException(Exception):
    pass


class LobbyInvite(BaseModel):
    """
    This model represents lobbies invites on Redis cache db.
    The Redis db keys from this model are described by a pair containing
    the from_user_id and the to_user_id in a set of lobby invites list:

    [zset] __mm:lobby:[lobby_id]:invites <from_player_id:to_player_id, timezone>
    """

    from_id: int
    to_id: int
    lobby_id: int

    class Config:
        CACHE_PREFIX: str = '__mm:lobby'

    @property
    def id(self):
        return f'{self.from_id}:{self.to_id}'

    @property
    def cache_key(self):
        return f'{LobbyInvite.Config.CACHE_PREFIX}:{self.lobby_id}:invites'

    @property
    def create_date(self):
        return timezone.datetime.fromtimestamp(cache.zscore(self.cache_key, self.id))

    @staticmethod
    def get(lobby_id: str, invite_id: str):
        invite = cache.zscore(
            f'{LobbyInvite.Config.CACHE_PREFIX}:{lobby_id}:invites', invite_id
        )

        if not invite:
            raise LobbyInviteException(_('Invite not found.'))

        from_id, to_id = invite_id.split(':')

        return LobbyInvite(
            from_id=int(from_id), to_id=int(to_id), lobby_id=int(lobby_id)
        )

    @staticmethod
    def get_all() -> List[LobbyInvite]:
        invites = []
        keys = cache.keys(f'{LobbyInvite.Config.CACHE_PREFIX}:*:invites')
        for key in keys:
            lobby_id = key.split(':')[2]
            lobby_invites = cache.zrange(key, 0, -1)
            for invite_id in lobby_invites:
                from_id, to_id = invite_id.split(':')
                invites.append(
                    LobbyInvite(
                        from_id=int(from_id), to_id=int(to_id), lobby_id=int(lobby_id)
                    )
                )

        return invites

    @staticmethod
    def get_by_to_user_id(to_user_id: int) -> List[LobbyInvite]:
        all_invites = LobbyInvite.get_all()
        to_invites = []
        for invite in all_invites:
            if to_user_id == invite.to_id:
                to_invites.append(invite)

        return to_invites

    @staticmethod
    def get_by_from_user_id(from_user_id: int) -> List[LobbyInvite]:
        all_invites = LobbyInvite.get_all()
        to_invites = []
        for invite in all_invites:
            if from_user_id == invite.from_id:
                to_invites.append(invite)

        return to_invites

    @staticmethod
    def get_by_id(invite_id: str) -> LobbyInvite:
        all_invites = LobbyInvite.get_all()
        for invite in all_invites:
            if invite_id == invite.id:
                return invite

        raise LobbyInviteException(_('Invite not found.'))
