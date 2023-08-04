from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase
from profiles.api import controller


class ProfilesControllerTestCase(VerifiedAccountsMixin, TestCase):
    def test_detail(self):
        profile = controller.detail(user_id=self.user_1.id)
        self.assertEqual(profile.user.id, self.user_1.id)

        profile = controller.detail(steamid=self.user_1.account.steamid)
        self.assertEqual(profile.user.id, self.user_1.id)
