from core.tests import TestCase

from ..api.authorization import is_verified
from .mixins import VerifiedAccountsMixin


class AuthorizationTestCase(VerifiedAccountsMixin, TestCase):
    def test_is_verified_is_true(self):
        self.assertTrue(is_verified(self.user_1))

    def test_is_verified_is_false(self):
        self.user_1.account.is_verified = False
        self.user_1.account.save()

        self.assertFalse(is_verified(self.user_1))
