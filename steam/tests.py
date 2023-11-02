from accounts.tests.mixins import UserOneMixin
from core.tests import TestCase

from . import Steam


class SteamTestCase(UserOneMixin, TestCase):
    def test_build_avatar_url(self):
        # TODO maybe we should test regex
        avatar = Steam.build_avatar_url(hash='12345', size=None)
        expected_url = f'{Steam.AVATARS_URL}/12/12345.jpg'
        self.assertEqual(avatar, expected_url)

        avatar = Steam.build_avatar_url(hash='6789', size='medium')
        expected_url = f'{Steam.AVATARS_URL}/67/6789_medium.jpg'
        self.assertEqual(avatar, expected_url)

        avatar = Steam.build_avatar_url(hash='09876', size='full')
        expected_url = f'{Steam.AVATARS_URL}/09/09876_full.jpg'
        self.assertEqual(avatar, expected_url)

        avatar = Steam.build_avatar_url()
        expected_url = f'{Steam.DEFAULT_AVATAR_URI}.jpg'
        self.assertEqual(avatar, expected_url)
