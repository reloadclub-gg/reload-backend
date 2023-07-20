from django.contrib.auth import get_user_model
from model_bakery import baker

from appsettings.services import player_max_level_points
from core.tests import TestCase

from .. import models, utils
from . import mixins

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

    def test_steamid64_to_hex(self):
        steamid64 = '56561198055990604'
        hexa = utils.steamid64_to_hex(steamid64)
        self.assertFalse(hexa.startswith('0x'))
        self.assertEqual(hexa, 'c8f21c2632a54c')

    def test_hex_to_steamid64(self):
        steamid_hex = 'c8f21c3e09b41c'
        steamid64 = utils.hex_to_steamid64(steamid_hex)
        self.assertEqual(steamid64, '56561198455960604')


class AccountsUtilsWithUsersTestCase(mixins.UserOneMixin, TestCase):
    def test_calc_level_and_points(self):
        account = baker.make(models.Account, user=self.user)
        points_earned = 30
        level, level_points = utils.calc_level_and_points(
            points_earned, account.level, account.level_points
        )
        self.assertEqual(level, account.level)
        self.assertEqual(level_points, account.level_points + points_earned)

        account.level = 1
        account.level_points = 95
        account.save()

        points_earned = 30
        level, level_points = utils.calc_level_and_points(
            points_earned, account.level, account.level_points
        )
        self.assertEqual(level, account.level + 1)
        self.assertEqual(
            level_points,
            account.level_points + points_earned - player_max_level_points(),
        )
