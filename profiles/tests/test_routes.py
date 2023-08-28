from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import APIClient, TestCase
from profiles.api import schemas


class ProfilesRoutesTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient('/api/profiles')

    def test_detail_user_id(self):
        self.user_1.auth.create_token()
        r = self.api.call(
            'get',
            f'/?user_id={self.user_2.id}',
            token=self.user_1.auth.token,
        )
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.ProfileSchema.from_orm(self.user_2.account).dict()
        self.assertEqual(r.json(), expected_response)

    def test_detail_steamid(self):
        self.user_1.auth.create_token()

        r = self.api.call(
            'get',
            f'/?steamid={self.user_2.steam_user.steamid}',
            token=self.user_1.auth.token,
        )
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.ProfileSchema.from_orm(self.user_2.account).dict()
        self.assertEqual(r.json(), expected_response)

    def test_detail_username(self):
        self.user_1.auth.create_token()

        r = self.api.call(
            'get',
            f'/?username={self.user_2.account.username}',
            token=self.user_1.auth.token,
        )
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.ProfileSchema.from_orm(self.user_2.account).dict()
        self.assertEqual(r.json(), expected_response)

        self.user_2.account.username = '!te;$t@'
        self.user_2.account.save()
        self.user_2.account.refresh_from_db()

        r = self.api.call(
            'get',
            f'/?username={self.user_2.account.username}',
            token=self.user_1.auth.token,
        )
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.ProfileSchema.from_orm(self.user_2.account).dict()
        self.assertEqual(r.json(), expected_response)

        r = self.api.call(
            'get',
            '/?username=%21te%3B%24t%40',
            token=self.user_1.auth.token,
        )
        self.assertEqual(r.status_code, 200)
        expected_response = schemas.ProfileSchema.from_orm(self.user_2.account).dict()
        self.assertEqual(r.json(), expected_response)

    def test_detail_not_found(self):
        self.user_1.auth.create_token()

        r = self.api.call(
            'get',
            f'/?steamid={123}',
            token=self.user_1.auth.token,
        )
        self.assertEqual(r.status_code, 404)

        r = self.api.call('get', f'/?user_id={123}', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 404)

    def test_update(self):
        self.user_1.auth.create_token()
        self.assertEqual(
            self.user_1.account.social_handles,
            {'twitch': None, 'discord': None, 'youtube': None},
        )
        self.api.call(
            'patch',
            '/',
            token=self.user_1.auth.token,
            data={
                'social_handles': {'twitch': 'username', 'othersocial': 'otherusername'}
            },
        )
        self.user_1.account.refresh_from_db()
        self.assertEqual(
            self.user_1.account.social_handles,
            {'twitch': 'username', 'discord': None, 'youtube': None},
        )
