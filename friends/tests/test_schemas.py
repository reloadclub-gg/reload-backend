from django.test import override_settings

from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase
from friends.api.schemas import FriendListSchema, FriendSchema


class FriendsSchemasTestCase(VerifiedAccountsMixin, TestCase):
    def test_friend_schema(self):
        payload = FriendSchema.from_orm(self.user_1.account).dict()
        expected_payload = {
            'user_id': self.user_1.id,
            'steamid': self.user_1.account.steamid,
            'level': self.user_1.account.level,
            'level_points': self.user_1.account.level_points,
            'username': self.user_1.steam_user.username,
            'avatar': self.user_1.account.avatar_dict,
            'status': self.user_1.status,
            'lobby_id': self.user_1.account.lobby.id
            if self.user_1.account.lobby
            else None,
            'steam_url': self.user_1.steam_user.profileurl,
        }
        self.assertEqual(payload, expected_payload)

    def test_friend_list_schema(self):
        payload = FriendListSchema.from_orm(
            {
                'requests': {'received': [], 'sent': []},
                'online': self.user_1.account.get_online_friends(),
                'offline': [
                    friend
                    for friend in self.user_1.account.friends
                    if not friend.user.is_online
                ],
            }
        ).dict()
        online_friends_count = len(self.user_1.account.get_online_friends())
        offline_friends_count = len(self.user_1.account.friends) - online_friends_count
        self.assertEqual(len(payload.get('online')), online_friends_count)
        self.assertEqual(len(payload.get('offline')), offline_friends_count)

    @override_settings(APP_GLOBAL_FRIENDSHIP=False)
    def test_friend_list_schema_no_friends(self):
        self.user_2.add_session()
        self.user_3.add_session()
        payload = FriendListSchema.from_orm(
            {
                'requests': {'received': [], 'sent': []},
                'online': self.user_1.account.get_online_friends(),
                'offline': [
                    friend
                    for friend in self.user_1.account.friends
                    if not friend.user.is_online
                ],
            }
        ).dict()
        online_friends_count = len(self.user_1.account.get_online_friends())
        offline_friends_count = len(self.user_1.account.friends) - online_friends_count
        self.assertEqual(len(payload.get('online')), online_friends_count)
        self.assertEqual(len(payload.get('offline')), offline_friends_count)
