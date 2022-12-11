from django.contrib.auth import get_user_model

from core.tests import TestCase
from .. import utils

User = get_user_model()


class AccountsTestUtilsTestCase(TestCase):
    def test_create_social_auth(self):
        user = User.objects.create(email='tester@email.com')
        social_auth = utils.create_social_auth(user)
        self.assertIsNotNone(user)
        self.assertIsNotNone(social_auth)
        self.assertIsNotNone(user.steam_user.steamid)
        self.assertEqual(
            social_auth.extra_data.get('player').get('steamid'), user.steam_user.steamid
        )

    def test_generate_steam_extra_data(self):
        extra_data = utils.generate_steam_extra_data()
        player = extra_data.get('player')
        self.assertIsNotNone(player)
        self.assertEqual(player.get('communityvisibilitystate'), 3)

        extra_data = utils.generate_steam_extra_data(public_profile=False).get('player')
        self.assertEqual(extra_data.get('communityvisibilitystate'), 0)
        self.assertEqual(len(extra_data.get('steamid')), 18)
        self.assertTrue(extra_data.get('steamid').isdigit())
        self.assertEqual(len(extra_data.get('personaname')), 9)
        self.assertFalse(extra_data.get('personaname').isdigit())

        extra_data = utils.generate_steam_extra_data(username='tester').get('player')
        self.assertEqual(extra_data.get('personaname'), 'tester')
