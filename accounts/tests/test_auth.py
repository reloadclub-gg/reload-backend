from core.tests import TestCase
from matchmaking.tests.mixins import SomePlayersMixin
from ..api.auth import is_verified


class AuthorizationTestCase(SomePlayersMixin, TestCase):
    def test_is_verified_is_true(self):
        self.assertTrue(is_verified(self.online_verified_user_1))

    def test_is_verified_is_false(self):
        self.online_verified_user_1.account.is_verified = False
        self.online_verified_user_1.account.save()

        self.assertFalse(is_verified(self.online_verified_user_1))
