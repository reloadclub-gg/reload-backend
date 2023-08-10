from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase
from profiles.api import controller, schemas


class ProfilesControllerTestCase(VerifiedAccountsMixin, TestCase):
    def test_detail(self):
        profile = controller.detail(user_id=self.user_1.id)
        self.assertEqual(profile.user.id, self.user_1.id)

        profile = controller.detail(steamid=self.user_1.account.steamid)
        self.assertEqual(profile.user.id, self.user_1.id)

    def test_update(self):
        self.assertEqual(
            self.user_1.account.social_handles,
            {'twitch': None, 'discord': None, 'youtube': None},
        )
        controller.update(
            self.user_1,
            schemas.ProfileUpdateSchema.from_orm(
                {'social_handles': {'twitch': 'username', 'other': 'otherusername'}}
            ),
        )
        self.assertEqual(
            self.user_1.account.social_handles,
            {'twitch': 'username', 'discord': None, 'youtube': None},
        )
        controller.update(
            self.user_1,
            schemas.ProfileUpdateSchema.from_orm(
                {'social_handles': {'twitch': None, 'other': 'otherusername'}}
            ),
        )
        self.assertEqual(
            self.user_1.account.social_handles,
            {'twitch': None, 'discord': None, 'youtube': None},
        )
