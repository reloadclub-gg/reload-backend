from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import APIClient, TestCase
from friends.api import schemas


class FriendsRoutesTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient('/api/friends')

    def test_friends_list(self):
        self.user_1.auth.create_token()
        r = self.api.call('get', '/', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.FriendListSchema.from_orm(
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
        self.assertEqual(r.json(), expected_response)
