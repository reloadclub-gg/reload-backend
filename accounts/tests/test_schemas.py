from accounts.api import schemas
from core.tests import TestCase
from lobbies.api.schemas import LobbySchema
from lobbies.models import Lobby
from matches.api.schemas import MatchSchema
from steam import Steam

from . import mixins


class AccountsSchemasTestCase(mixins.UserWithFriendsMixin, TestCase):
    def test_account_friend_schema(self):
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        payload = schemas.FriendAccountSchema.from_orm(self.user.account).dict()

        expected_payload = {
            'steamid': self.user.account.steamid,
            'level': self.user.account.level,
            'level_points': self.user.account.level_points,
            'id': self.user.id,
            'username': self.user.steam_user.username,
            'avatar': {
                'small': Steam.build_avatar_url(self.user.steam_user.avatarhash),
                'medium': Steam.build_avatar_url(
                    self.user.steam_user.avatarhash, 'medium'
                ),
                'large': Steam.build_avatar_url(
                    self.user.steam_user.avatarhash, 'full'
                ),
            },
            'is_online': self.user.is_online,
            'status': self.user.status,
            'lobby': LobbySchema.from_orm(self.user.account.lobby).dict(),
            'steam_url': self.user.steam_user.profileurl,
            'match': MatchSchema.from_orm(self.user.account.match)
            if self.user.account.match
            else None,
            'matches_played': len(self.user.account.matches_played),
            'latest_matches_results': self.user.account.get_latest_matches_results(),
        }

        self.assertDictEqual(payload, expected_payload)

    def test_account_schema(self):
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        payload = schemas.AccountSchema.from_orm(self.user.account).dict()

        expected_payload = {
            'steamid': self.user.account.steamid,
            'level': self.user.account.level,
            'level_points': self.user.account.level_points,
            'is_verified': self.user.account.is_verified,
            'username': self.user.steam_user.username,
            'avatar': {
                'small': Steam.build_avatar_url(self.user.steam_user.avatarhash),
                'medium': Steam.build_avatar_url(
                    self.user.steam_user.avatarhash, 'medium'
                ),
                'large': Steam.build_avatar_url(
                    self.user.steam_user.avatarhash, 'full'
                ),
            },
            'steam_url': self.user.steam_user.profileurl,
            'matches_played': len(self.user.account.matches_played),
            'latest_matches_results': self.user.account.get_latest_matches_results(),
        }

        self.assertDictEqual(payload, expected_payload)

    def test_user_schema(self):
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        payload = schemas.UserSchema.from_orm(self.user).dict()

        expected_payload = {
            'id': self.user.id,
            'email': self.user.email,
            'is_active': self.user.is_active,
            'account': schemas.AccountSchema.from_orm(self.user.account).dict(),
            'is_online': self.user.is_online,
            'status': self.user.status,
            'lobby_id': self.user.account.lobby.id,
            'match_id': self.user.account.match.id if self.user.account.match else None,
            'pre_match_id': self.user.account.pre_match.id
            if self.user.account.pre_match
            else None,
        }

        self.assertDictEqual(payload, expected_payload)
