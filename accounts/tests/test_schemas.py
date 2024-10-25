from accounts import models
from accounts.api import schemas
from core.tests import TestCase
from lobbies.models import Lobby
from matches.models import BetaUser

from . import mixins


class AccountsSchemasTestCase(mixins.UserWithFriendsMixin, TestCase):
    def test_account_schema(self):
        self.user.add_session()
        Lobby.create(self.user.id)
        payload = schemas.AccountSchema.from_orm(self.user.account).dict()

        expected_payload = {
            "steamid": self.user.account.steamid,
            "level": self.user.account.level,
            "level_points": self.user.account.level_points,
            "is_verified": self.user.account.is_verified,
            "username": self.user.steam_user.username,
            "avatar": self.user.account.avatar_dict,
            "coins": self.user.account.coins,
        }

        self.assertDictEqual(payload, expected_payload)

    def test_user_schema(self):
        self.user.add_session()
        Lobby.create(self.user.id)
        payload = schemas.UserSchema.from_orm(self.user).dict()

        expected_payload = {
            "id": self.user.id,
            "email": self.user.email,
            "is_active": self.user.is_active,
            "account": schemas.AccountSchema.from_orm(self.user.account).dict(),
            "is_online": self.user.is_online,
            "status": self.user.status,
            "lobby_id": self.user.account.lobby.id,
            "match_id": (
                self.user.account.get_match().id
                if self.user.account.get_match()
                else None
            ),
            "pre_match_id": (
                self.user.account.pre_match.id if self.user.account.pre_match else None
            ),
            "invites": [],
            "invites_available_count": models.Invite.MAX_INVITES_PER_ACCOUNT,
            "is_beta": BetaUser.objects.filter(email=self.user.email).exists(),
            "is_alpha": self.user.is_alpha,
            "feats": [],
        }

        self.assertDictEqual(payload, expected_payload)
