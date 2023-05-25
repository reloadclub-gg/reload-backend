from core.tests import APIClient, TestCase
from matchmaking.tests.mixins import VerifiedPlayersMixin
from profiles.api import schemas


class ProfilesRoutesTestCase(VerifiedPlayersMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient('/api/profiles')

    def test_detail(self):
        self.user_1.auth.create_token()
        r = self.api.call(
            'get', f'/', token=self.user_1.auth.token, data={'user_id': self.user_2.id}
        )
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.ProfileSchema.from_orm(self.user_2.account).dict()
        self.assertEqual(r.json(), expected_response)

        r = self.api.call(
            'get',
            f'/',
            token=self.user_1.auth.token,
            data={'steamid': self.user_2.steam_user.steamid},
        )
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.ProfileSchema.from_orm(self.user_2.account).dict()
        self.assertEqual(r.json(), expected_response)

        r = self.api.call(
            'get',
            f'/',
            token=self.user_1.auth.token,
            data={'steamid': 123},
        )
        self.assertEqual(r.status_code, 404)

        r = self.api.call(
            'get',
            f'/',
            token=self.user_1.auth.token,
            data={'user_id': 123},
        )
        self.assertEqual(r.status_code, 404)
