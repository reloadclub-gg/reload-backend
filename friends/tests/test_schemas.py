from core.tests import TestCase
from friends.api.schemas import FriendListSchema, FriendSchema
from matchmaking.tests.mixins import VerifiedPlayersMixin
from steam import Steam


class FriendsSchemasTestCase(VerifiedPlayersMixin, TestCase):
    def test_friend_schema(self):
        payload = FriendSchema.from_orm(self.user_1.account).dict()
        expected_payload = {
            'steamid': self.user_1.account.steamid,
            'level': self.user_1.account.level,
            'level_points': self.user_1.account.level_points,
            'user_id': self.user_1.id,
            'username': self.user_1.steam_user.username,
            'avatar': {
                'small': Steam.build_avatar_url(self.user_1.steam_user.avatarhash),
                'medium': Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'medium'
                ),
                'large': Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'full'
                ),
            },
            'status': self.user_1.status,
            'lobby_id': self.user_1.account.lobby.id
            if self.user_1.account.lobby
            else None,
            'steam_url': self.user_1.steam_user.profileurl,
            'matches_played': len(self.user_1.account.matches_played),
            'latest_matches_results': self.user_1.account.get_latest_matches_results(),
        }
        self.assertEqual(payload, expected_payload)

    def test_friend_list_schema(self):
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        payload = FriendListSchema.from_orm(
            {
                'online': self.user_1.account.online_friends,
                'offline': [
                    friend
                    for friend in self.user_1.account.friends
                    if not friend.user.is_online
                ],
            }
        ).dict()
        self.assertEqual(len(payload.get('online')), 2)
        self.assertEqual(len(payload.get('offline')), 13)
