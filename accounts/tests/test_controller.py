from unittest import mock

from django.http import Http404
from model_bakery import baker
from ninja import Schema
from ninja.errors import HttpError

from appsettings.models import AppSettings
from core.tests import TestCase
from lobbies.models import Lobby
from matchmaking.tests.mixins import VerifiedPlayersMixin

from .. import utils
from ..api import controller
from ..models import Account, Auth, Invite, User, UserLogin
from . import mixins


class AccountSchema(Schema):
    is_verified: bool = False


class UserSchema(Schema):
    id: int = None
    account: AccountSchema = None


class RequestSchema(Schema):
    user: UserSchema = None
    META: dict = {'HTTP_X_FORWARDED_FOR': '111.111.111.111'}


class RequestExemptSchema(RequestSchema):
    verified_exempt: bool = True


class AccountsControllerTestCase(mixins.AccountOneMixin, TestCase):
    def test_login_is_verified(self):
        self.user.account.is_verified = True
        self.user.account.save()
        auth = Auth(user_id=self.user.id, force_token_create=True)
        controller.login(RequestSchema(), auth.token)
        self.user.refresh_from_db()
        logins = UserLogin.objects.filter(user=self.user)
        self.assertTrue(logins.exists())
        self.assertEqual(logins[0].ip_address, '111.111.111.111')

    def test_login_isnt_verified(self):
        self.user.account.is_verified = False
        self.user.account.save()
        auth = Auth(user_id=self.user.id, force_token_create=True)
        controller.login(RequestExemptSchema(), auth.token)
        self.user.refresh_from_db()
        logins = UserLogin.objects.filter(user=self.user)
        self.assertTrue(logins.exists())
        self.assertEqual(logins[0].ip_address, '111.111.111.111')

    def test_create_fake_user(self):
        user = controller.create_fake_user(email='fake-tester@email.com')
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'fake-tester@email.com')
        self.assertIsNotNone(user.social_auth)
        self.assertIsNotNone(user.steam_user.steamid)

    @mock.patch('accounts.utils.send_verify_account_mail')
    def test_signup(self, mocker):
        invite = baker.make(Invite, owned_by=self.account, email='invited@email.com')
        user = baker.make(User, email=invite.email)
        utils.create_social_auth(user)

        controller.signup(user, email=user.email)
        invite.refresh_from_db()

        self.assertTrue(hasattr(user, 'account'))
        self.assertIsNotNone(invite.datetime_accepted)

        mocker.assert_called_once()
        mocker.assert_called_once_with(
            user.email, user.steam_user.username, user.account.verification_token
        )

    def test_signup_not_invited(self):
        AppSettings.set_bool('Invite Required', True)
        user = baker.make(User)
        with self.assertRaises(HttpError):
            controller.signup(user, email=user.email)

    @mock.patch('accounts.utils.send_welcome_mail')
    @mock.patch('accounts.api.controller.ws_new_notification')
    def test_verify_account(self, mock_new_notification, mock_welcome_email):
        controller.verify_account(self.user, self.user.account.verification_token)
        self.user.refresh_from_db()
        self.assertTrue(self.user.account.is_verified)
        self.assertIsNone(self.user.auth.sessions)

        mock_new_notification.assert_not_called()

        mock_welcome_email.assert_called_once()
        mock_welcome_email.assert_called_once_with(self.user.email)

    def test_verify_account_already_verified(self):
        self.user.account.is_verified = True
        self.user.account.save()
        with self.assertRaises(HttpError):
            controller.verify_account(self.user, self.user.account.verification_token)

    @mock.patch('accounts.utils.send_inactivation_mail')
    def test_inactivate(self, mocker):
        self.user.auth.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)
        self.assertTrue(self.user.is_active)
        controller.inactivate(self.user)
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.date_inactivation)

        mocker.assert_called_once()
        mocker.assert_called_once_with(self.user.email)

    @mock.patch('accounts.utils.send_verify_account_mail')
    def test_update_email(self, mocker):
        self.user.account.is_verified = True
        self.user.account.save()
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        controller.update_email(self.user, 'new@email.com')
        self.assertFalse(self.user.account.is_verified)
        self.assertEqual(self.user.email, 'new@email.com')

        mocker.assert_called_once()
        mocker.assert_called_once_with(
            self.user.email,
            self.user.steam_user.username,
            self.user.account.verification_token,
        )

    @mock.patch(
        'accounts.utils.send_verify_account_mail',
        return_value=True,
    )
    def test_update_email_should_send_verification_email(self, mocker):
        self.user.account.is_verified = True
        self.user.account.save()
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        controller.update_email(self.user, 'new@email.com')
        mocker.assert_called_once()

    @mock.patch('accounts.api.controller.websocket.ws_user_logout')
    def test_logout(self, mock_user_logout):
        self.user.auth.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)
        self.assertEqual(self.user.account.lobby.id, self.user.id)

        controller.logout(self.user)
        self.assertIsNone(self.user.account.lobby)
        self.assertFalse(self.user.is_online)

        mock_user_logout.assert_called_once()

    def test_logout_other_lobby(self):
        self.user.auth.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)

        another_user = User.objects.create_user(
            "hulk@avengers.com",
            "hulkbuster",
        )
        utils.create_social_auth(another_user)
        baker.make(Account, user=another_user)
        another_user.auth.add_session()
        another_user.account.is_verified = True
        another_user.account.save()
        lobby_2 = Lobby.create(another_user.id)
        lobby_2.invite(another_user.id, self.user.id)
        Lobby.move(self.user.id, lobby_2.id)

        self.assertEqual(self.user.account.lobby.id, lobby_2.id)

        controller.logout(self.user)

        self.assertIsNone(self.user.account.lobby)
        self.assertFalse(self.user.is_online)


class AccountsControllerVerifiedPlayersTestCase(VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()

    @mock.patch('accounts.api.controller.ws_expire_player_invites')
    @mock.patch('accounts.api.controller.ws_friend_update_or_create')
    @mock.patch('accounts.api.controller.player_move')
    def test_logout_lobby_owner(
        self,
        mock_expire_player_invites,
        mock_friend_create_or_update,
        mock_player_move,
    ):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)

        lobby_1.invite(self.user_1.id, self.user_6.id)

        lobby_1.set_public()
        Lobby.move(self.user_2.id, lobby_1.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        Lobby.move(self.user_4.id, lobby_1.id)
        Lobby.move(self.user_5.id, lobby_1.id)

        controller.logout(self.user_1)
        mock_expire_player_invites.assert_called_once()
        mock_friend_create_or_update.assert_called_once()
        mock_player_move.assert_called_once()

    def test_user_matches(self):
        self.assertCountEqual(
            self.user_1.account.matches_played, controller.user_matches(self.user_1.id)
        )

        with self.assertRaises(Http404):
            controller.user_matches(597865)

    @mock.patch('accounts.api.controller.ws_friend_update_or_create')
    def test_auth(self, mock_friend_update_or_create):
        self.user_1.auth.remove_session()
        self.user_1.auth.expire_session(seconds=0)

        controller.auth(self.user_1)
        mock_friend_update_or_create.assert_called_once()
        self.assertIsNotNone(self.user_1.auth.sessions)
        self.assertIsNotNone(self.user_1.account.lobby)

    @mock.patch('accounts.api.controller.ws_friend_update_or_create')
    def test_auth_unverified(self, mock_friend_update_or_create):
        self.user_1.account.is_verified = False
        self.user_1.account.save()
        self.user_1.refresh_from_db()

        self.user_1.auth.remove_session()
        self.user_1.auth.expire_session(seconds=0)

        controller.auth(self.user_1)
        mock_friend_update_or_create.assert_not_called()
        self.assertIsNone(self.user_1.auth.sessions)
        self.assertIsNone(self.user_1.account.lobby)

    @mock.patch('accounts.api.controller.ws_friend_update_or_create')
    def test_auth_no_account(self, mock_friend_update_or_create):
        self.user_1.account.delete()
        self.user_1.refresh_from_db()

        self.user_1.auth.remove_session()
        self.user_1.auth.expire_session(seconds=0)

        controller.auth(self.user_1)
        mock_friend_update_or_create.assert_not_called()
        self.assertIsNone(self.user_1.auth.sessions)
        self.assertFalse(hasattr(self.user_1, 'account'))

    @mock.patch('accounts.api.controller.ws_friend_update_or_create')
    def test_auth_with_session(self, mock_friend_update_or_create):
        controller.auth(self.user_1)
        mock_friend_update_or_create.assert_not_called()
        self.assertIsNotNone(self.user_1.auth.sessions)
        self.assertEqual(self.user_1.auth.sessions, 2)
        self.assertIsNotNone(self.user_1.account.lobby)

    @mock.patch('accounts.models.auth.Auth.add_session')
    @mock.patch('accounts.models.auth.Auth.persist_session')
    def test_auth_persists_session(self, mock_persist_session, mock_add_session):
        controller.auth(self.user_1)
        mock_persist_session.assert_called_once()
        mock_add_session.assert_called_once()
        self.assertEqual(self.user_1.auth.sessions_ttl, -1)

    @mock.patch('accounts.api.controller.ws_new_notification')
    @mock.patch('accounts.api.controller.cache.sadd')
    def test_verify_account_with_online_friends(
        self,
        mock_friends_cache,
        mock_new_notification,
    ):
        self.user_1.account.is_verified = False
        self.user_1.account.save()
        self.user_1.refresh_from_db()
        self.assertEqual(len(self.user_2.account.online_friends), 4)
        controller.verify_account(self.user_1, self.user_1.account.verification_token)
        self.assertEqual(len(self.user_2.account.online_friends), 5)
        mock_friends_cache_calls = [
            mock.call(f'__friendlist:user:{self.user_2.id}', self.user_1.id),
            mock.call(f'__friendlist:user:{self.user_3.id}', self.user_1.id),
            mock.call(f'__friendlist:user:{self.user_4.id}', self.user_1.id),
            mock.call(f'__friendlist:user:{self.user_5.id}', self.user_1.id),
            mock.call(f'__friendlist:user:{self.user_6.id}', self.user_1.id),
        ]
        mock_friends_cache.assert_has_calls(mock_friends_cache_calls)
        self.assertEqual(mock_new_notification.call_count, 5)
