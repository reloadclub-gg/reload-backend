from unittest import mock

from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase
from friends.api import controller


class FriendsControllerTestCase(VerifiedAccountsMixin, TestCase):
    @mock.patch('friends.api.controller.Steam.get_player_friends')
    def test_fetch_steam_friends_empty(self, mock_get_friends):
        mock_get_friends.return_value = []
        response = controller.fetch_steam_friends(self.user_1)
        self.assertEqual(list(response), [])

    @mock.patch('friends.api.controller.Steam.get_player_friends')
    def test_fetch_steam_friends(self, mock_get_friends):
        mock_get_friends.return_value = [
            {
                'steamid': self.user_2.steam_user.steamid,
                'relationship': 'friend',
                'friend_since': 1635963090,
            }
        ]
        response = controller.fetch_steam_friends(self.user_1)
        self.assertEqual(list(response), [self.user_2.account])
