from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase
from friends.api.schemas import FriendSchema
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

    def test_search(self):
        result = controller.search(self.user_1.account.username)
        self.assertEqual(result, [FriendSchema.from_orm(self.user_1.account)])

        result = controller.search('user_')
        self.assertEqual(len(result), 25)

        result = controller.search('@example')
        self.assertEqual(len(result), 26)

        result = controller.search('offline_verified_user')
        self.assertEqual(
            result,
            [FriendSchema.from_orm(self.offline_verified_user.account)],
        )
