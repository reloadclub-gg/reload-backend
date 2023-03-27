from unittest import mock

from django.core.exceptions import ValidationError
from django.utils import timezone
from model_bakery import baker
from social_django.models import UserSocialAuth

from core.tests import TestCase, cache
from matchmaking.models import Lobby

from .. import models, utils
from ..models.auth import AuthConfig
from . import mixins


class AccountsAccountModelTestCase(mixins.UserOneMixin, TestCase):
    def __create_friend(self):
        user = baker.make(models.User)
        baker.make(
            UserSocialAuth, user=user, extra_data=utils.generate_steam_extra_data()
        )
        return user

    def test_account_verification_token(self):
        account = baker.make(models.Account, user=self.user)
        self.assertIsNotNone(account.verification_token)
        self.assertEqual(account.verification_token, account.DEBUG_VERIFICATION_TOKEN)

    def test_account_save(self):
        user = baker.make(models.User)
        account = models.Account(user=user)
        self.assertRaises(ValidationError, account.save)

    @mock.patch('steam.SteamClient.get_friends')
    def test_friends(self, mock_friends):
        f1 = self.__create_friend()
        baker.make(models.Account, user=f1, is_verified=True)

        f2 = self.__create_friend()
        baker.make(models.Account, user=f2)

        mock_friends.return_value = [
            {
                'steamid': f1.steam_user.steamid,
                'relationship': 'friend',
                'friend_since': 1635963090,
            },
            {
                'steamid': f2.steam_user.steamid,
                'relationship': 'friend',
                'friend_since': 1637350627,
            },
            {
                'steamid': '12345678901234',
                'relationship': 'friend',
                'friend_since': 1637350627,
            },
        ]

        baker.make(models.Account, user=self.user)
        self.assertEqual(len(self.user.account.friends), 1)
        self.assertEqual(self.user.account.friends[0].user.email, f1.email)

    @mock.patch('steam.SteamClient.get_friends')
    def test_online_friends(self, mock_friends):
        f1 = self.__create_friend()
        baker.make(models.Account, user=f1, is_verified=True)

        f2 = self.__create_friend()
        baker.make(models.Account, user=f2)

        mock_friends.return_value = [
            {
                'steamid': f1.steam_user.steamid,
                'relationship': 'friend',
                'friend_since': 1635963090,
            },
            {
                'steamid': f2.steam_user.steamid,
                'relationship': 'friend',
                'friend_since': 1637350627,
            },
            {
                'steamid': '12345678901234',
                'relationship': 'friend',
                'friend_since': 1637350627,
            },
        ]

        baker.make(models.Account, user=self.user)
        f1.auth.add_session()
        self.assertEqual(len(self.user.account.online_friends), 1)

    def test_set_level_points(self):
        account = baker.make(models.Account, user=self.user)
        self.assertEqual(account.level, 0)
        self.assertEqual(account.level_points, 0)
        self.assertFalse(account.second_chance_lvl)

        account.set_level_points(35)
        self.assertEqual(account.level, 0)
        self.assertEqual(account.level_points, 35)
        self.assertTrue(account.second_chance_lvl)

        account.set_level_points(90)
        self.assertEqual(account.level, 1)
        self.assertEqual(account.level_points, 25)
        self.assertTrue(account.second_chance_lvl)

        account.set_level_points(-30)
        self.assertEqual(account.level, 1)
        self.assertEqual(account.level_points, 0)
        self.assertFalse(account.second_chance_lvl)

        account.set_level_points(-15)
        self.assertEqual(account.level, 0)
        self.assertEqual(account.level_points, 85)
        self.assertTrue(account.second_chance_lvl)

        account.set_level_points(-90)
        self.assertEqual(account.level, 0)
        self.assertEqual(account.level_points, 0)

        with self.assertRaises(ValidationError):
            account.set_level_points(310)

        with self.assertRaises(ValidationError):
            account.set_level_points(-310)


class AccountsInviteModelTestCase(mixins.AccountOneMixin, TestCase):
    def test_invite_create_limit_reached(self):
        baker.make(
            models.Invite,
            owned_by=self.account,
            _quantity=models.Invite.MAX_INVITES_PER_ACCOUNT,
        )

        invite = models.Invite(email='extra@email.com', owned_by=self.account)
        self.assertRaises(ValidationError, invite.clean)

        self.user.is_staff = True
        self.user.save()
        invite = models.Invite(email='extra@email.com', owned_by=self.account)
        invite.clean()

    def test_invite_create_existing_email(self):
        invite = models.Invite(email=self.user.email, owned_by=self.account)
        self.assertRaises(ValidationError, invite.clean)

    def test_invite_update(self):
        invite = baker.make(models.Invite, owned_by=self.account)
        self.assertIsNone(invite.datetime_accepted)
        invite.datetime_accepted = timezone.now()
        invite.save()

        invite.email = 'other@email.com'
        self.assertRaises(ValidationError, invite.clean)


class AccountsUserModelTestCase(mixins.VerifiedAccountMixin, TestCase):
    def test_user_steam_user(self):
        user = baker.make(models.User)
        self.assertIsNone(user.steam_user)
        self.assertIsNotNone(self.user.steam_user)

    def test_user_auth(self):
        self.assertIsNotNone(self.user.auth)
        self.user.auth.add_session()
        self.assertEqual(self.user.auth.sessions, 1)

    def test_is_online(self):
        self.assertFalse(self.user.is_online)
        self.user.auth.add_session()
        self.assertTrue(self.user.is_online)
        self.user.auth.remove_session()
        self.assertTrue(self.user.is_online)

    def test_user_status(self):
        self.assertEqual(self.user.status, 'offline')
        self.user.auth.add_session()
        self.assertEqual(self.user.status, 'online')
        Lobby.create(self.user.id)
        self.assertEqual(self.user.status, 'online')

        with mock.patch(
            'matchmaking.models.lobby.Lobby.players_count',
            new_callable=mock.PropertyMock,
        ) as mocker:
            mocker.return_value = 2
            self.assertEqual(self.user.status, 'teaming')

        self.user.account.lobby.start_queue()
        self.assertEqual(self.user.status, 'queued')
        self.user.account.lobby.cancel_queue()
        self.assertEqual(self.user.status, 'online')

    def test_inactivate(self):
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.date_inactivation)
        self.user.inactivate()
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.date_inactivation)


class AccountsAuthModelTestCase(mixins.AccountOneMixin, TestCase):
    def test_token_init(self):
        auth = models.Auth(user_id=self.user.id)
        auth.create_token()
        self.assertIsNotNone(cache.get(auth.token_cache_key))

    def test_token_create(self):
        auth = models.Auth(user_id=self.user.id)
        self.assertIsNone(cache.get(auth.token_cache_key))
        auth.create_token()
        self.assertIsNotNone(cache.get(auth.token_cache_key))

    def test_token_auto_create(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        self.assertIsNotNone(cache.get(auth.token_cache_key))

    def test_token_load(self):
        created = models.Auth(user_id=self.user.id, force_token_create=True)
        loaded = models.Auth.load(created.token)
        self.assertEqual(loaded.token, created.token)

    def test_sessions(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        self.assertIsNone(auth.sessions)

    def test_sessions_add(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        auth.add_session()
        self.assertEqual(auth.sessions, 1)

    def test_sessions_remove(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        auth.add_session()
        auth.add_session()
        auth.remove_session()
        self.assertEqual(auth.sessions, 1)

    def test_sessions_set_expire(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        auth.add_session()
        auth.expire_session()
        self.assertEqual(auth.sessions_ttl, AuthConfig.CACHE_TTL_SESSIONS)
