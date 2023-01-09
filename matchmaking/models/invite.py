from pydantic import BaseModel


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
