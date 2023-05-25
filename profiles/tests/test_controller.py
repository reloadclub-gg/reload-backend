from unittest import mock

from ninja.errors import Http404, HttpError

from core.tests import TestCase
from matchmaking.tests.mixins import VerifiedPlayersMixin
from profiles.api import controller


class ProfilesControllerTestCase(VerifiedPlayersMixin, TestCase):
    def test_detail(self):
        user = controller.detail(user_id=self.user_1.id)
        self.assertEqual(user.id, self.user_1.id)

        user = controller.detail(steamid=int(self.user_1.steam_user.steamid))
        self.assertEqual(user.id, self.user_1.id)
