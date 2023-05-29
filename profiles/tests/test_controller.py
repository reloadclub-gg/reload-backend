from core.tests import TestCase
from matchmaking.tests.mixins import VerifiedPlayersMixin
from profiles.api import controller


class ProfilesControllerTestCase(VerifiedPlayersMixin, TestCase):
    def test_detail(self):
        profile = controller.detail(user_id=self.user_1.id)
        self.assertEqual(profile.user.id, self.user_1.id)

        profile = controller.detail(steamid=int(self.user_1.steam_user.steamid))
        self.assertEqual(profile.user.id, self.user_1.id)
