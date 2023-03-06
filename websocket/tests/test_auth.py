from accounts.models.auth import AuthConfig
from accounts.tests.mixins import AccountOneMixin
from core.tests import TestCase
from websocket import auth


class WSAuthTestCase(AccountOneMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user.account.is_verified = True
        self.user.account.save()
        self.user.auth.create_token()

    def test_authenticate(self):
        scope = {'query_string': f'anyurl.com/?token={self.user.auth.token}'}
        user = auth.authenticate(scope)
        self.assertEqual(self.user.id, user.id)
        self.assertEqual(self.user.auth.sessions_ttl, -1)

    def test_authenticate_fail(self):
        scope = {'query_string': '?token=any_token'}
        user = auth.authenticate(scope)
        self.assertIsNone(user)

    def test_disconnect(self):
        self.user.auth.add_session()
        auth.disconnect(self.user)
        self.assertEqual(self.user.auth.sessions_ttl, AuthConfig.CACHE_TTL_SESSIONS)

        self.user.auth.expire_session(0)
        self.user.auth.add_session()
        self.user.auth.add_session()
        auth.disconnect(self.user)
        self.assertEqual(self.user.auth.sessions, 1)
        self.assertEqual(self.user.auth.sessions_ttl, -1)
