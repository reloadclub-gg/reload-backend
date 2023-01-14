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

    [set] __mm:lobby:[player_id]:invites <(from_player_id:to_player_id,...)>
    """

    from_id: int
    to_id: int
    lobby_id: int

    @property
    def id(self):
        return f'{self.from_id}:{self.to_id}'

    class Config:
        CACHE_PREFIX: str = '__mm:lobby'

    @staticmethod
    def get(lobby_id: str, invite_id: str):
        invite = cache.sismember(
            f'{LobbyInvite.Config.CACHE_PREFIX}:{lobby_id}:invites', invite_id
        )

        if not invite:
            raise LobbyInviteException('Inexistent invite caught on invite deletion')

        from_id, to_id = invite_id.split(':')

        return LobbyInvite(
            from_id=int(from_id), to_id=int(to_id), lobby_id=int(lobby_id)
        )
