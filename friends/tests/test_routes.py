from core.tests import APIClient, TestCase
from friends.api import schemas
from matchmaking.tests.mixins import VerifiedPlayersMixin


class FriendsRoutesTestCase(VerifiedPlayersMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient('/api/friends')

    def test_friends_list(self):
        self.user_1.auth.create_token()
        r = self.api.call('get', '/', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.FriendListSchema.from_orm(
            {
                'online': self.user_1.account.online_friends,
                'offline': [
                    friend
                    for friend in self.user_1.account.friends
                    if not friend.user.is_online
                ],
            }
        )
        self.assertEqual(r.json(), expected_response)

    def test_friends_detail(self):
        self.user_1.auth.create_token()
        r = self.api.call('get', f'/{self.user_2.id}/', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.FriendSchema.from_orm(self.user_2.account).dict()
        self.assertEqual(r.json(), expected_response)
