from accounts.models.auth import Auth
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

    def test_authenticate_fail(self):
        scope = {'query_string': '?token=any_token'}
        user = auth.authenticate(scope)
        self.assertIsNone(user)

    def test_authenticate_unverified(self):
        self.user.account.is_verified = False
        self.user.account.save()

        scope = {'query_string': f'anyurl.com/?token={self.user.auth.token}'}
        user = auth.authenticate(scope)
        self.assertIsNone(user)

    def test_authenticate_no_account(self):
        self.user.account.delete()
        self.user.refresh_from_db()

        scope = {'query_string': f'anyurl.com/?token={self.user.auth.token}'}
        user = auth.authenticate(scope)
        self.assertIsNone(user)

    def test_disconnect(self):
        self.user.add_session()
        auth.disconnect(self.user)
        self.assertEqual(self.user.auth.sessions_ttl, Auth.Config.SESSION_GAP_TTL)

        self.user.logout()
        self.user.add_session()
        self.user.add_session()
        auth.disconnect(self.user)
        self.assertEqual(self.user.auth.sessions, 1)

        auth.disconnect(self.user)
        self.assertEqual(self.user.auth.sessions, 0)
