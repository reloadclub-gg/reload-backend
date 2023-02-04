from unittest import mock

from model_bakery import baker
from ninja import Schema
from ninja.errors import HttpError

from appsettings.models import AppSettings
from core.tests import TestCase
from matchmaking.models import Lobby

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

    def test_signup(self):
        invite = baker.make(Invite, owned_by=self.account, email='invited@email.com')
        user = baker.make(User, email=invite.email)
        utils.create_social_auth(user)

        controller.signup(user, email=user.email)
        invite.refresh_from_db()

        self.assertTrue(hasattr(user, 'account'))
        self.assertIsNotNone(invite.datetime_accepted)

    def test_signup_not_invited(self):
        AppSettings.set_bool('Invite Required', True)
        user = baker.make(User)
        with self.assertRaises(HttpError):
            controller.signup(user, email=user.email)

    def test_verify_account(self):
        controller.verify_account(self.user, self.user.account.verification_token)
        self.user.refresh_from_db()
        self.assertTrue(self.user.account.is_verified)
        self.assertIsNone(self.user.auth.sessions)

    def test_verify_account_already_verified(self):
        self.user.account.is_verified = True
        self.user.account.save()
        with self.assertRaises(HttpError):
            controller.verify_account(self.user, self.user.account.verification_token)

    def test_inactivate(self):
        self.user.auth.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)
        self.assertTrue(self.user.is_active)
        controller.inactivate(self.user)
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.date_inactivation)

    def test_update_email(self):
        self.user.account.is_verified = True
        self.user.account.save()
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        controller.update_email(self.user, 'new@email.com')
        self.assertFalse(self.user.account.is_verified)
        self.assertEqual(self.user.email, 'new@email.com')

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

    def test_logout(self):
        self.user.auth.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)

        self.assertEqual(self.user.account.lobby.id, self.user.id)

        user_offline = controller.logout(self.user)

        self.assertIsNone(user_offline.account.lobby)
        self.assertFalse(user_offline.is_online)

    def test_logout_lobby(self):
        # TODO
        pass

    def test_logout_other_lobby(self):
        self.user.auth.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        lobby_1 = Lobby.create(self.user.id)

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
        lobby_2.invite(another_user.id, lobby_1.id)
        Lobby.move(lobby_1.id, lobby_2.id)

        self.assertEqual(self.user.account.lobby.id, lobby_2.id)

        user_offline = controller.logout(self.user)

        self.assertIsNone(user_offline.account.lobby)
        self.assertFalse(user_offline.is_online)
