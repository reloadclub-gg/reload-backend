from core.tests import TestCase
from matchmaking.tests.mixins import SomePlayersMixin
from ..api.auth import is_not_verified


class AuthorizationTestCase(SomePlayersMixin, TestCase):
    def test_is_not_verified_is_true(self):
        self.online_verified_user_1.account.is_verified = False
        self.online_verified_user_1.account.save()

        self.assertTrue(is_not_verified(self.online_verified_user_1))

    def test_is_not_verified_is_false(self):
        self.assertFalse(is_not_verified(self.online_verified_user_1))
