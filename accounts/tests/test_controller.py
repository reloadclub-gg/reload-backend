from unittest import mock

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from model_bakery import baker
from ninja import Schema
from ninja.errors import HttpError

from appsettings.models import AppSettings
from core.tests import TestCase
from lobbies.models import Lobby
from matches.models import BetaUser

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
        invite_required = AppSettings.objects.get(name='Invite Required')
        invite_required.value = '1'
        invite_required.save()
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
        invite_required = AppSettings.objects.get(name='Invite Required')
        invite_required.value = '1'
        invite_required.save()
        user = baker.make(User)
        with self.assertRaises(HttpError):
            controller.signup(user, email=user.email)

    def test_signup_on_beta(self):
        beta_required = AppSettings.objects.get(name='Beta Required')
        beta_required.value = '1'
        beta_required.save()

        user = baker.make(User)
        utils.create_social_auth(user)

        with self.assertRaises(HttpError):
            controller.signup(user, email=user.email)

        invite_required = AppSettings.objects.get(name='Invite Required')
        invite_required.value = '1'
        invite_required.save()

        signed_user = baker.make(User)
        utils.create_social_auth(signed_user)
        signed_account = baker.make(Account, user=signed_user, is_verified=True)
        Invite.objects.create(owned_by=signed_account, email=user.email)

        with self.assertRaises(HttpError):
            controller.signup(user, email=user.email)

        baker.make(BetaUser, email=user.email)
        controller.signup(user, email=user.email)

    def test_signup_on_alpha(self):
        alpha_required = AppSettings.objects.get(name='Alpha Required')
        alpha_required.value = '1'
        alpha_required.save()

        user = baker.make(User)
        utils.create_social_auth(user)

        with self.assertRaises(HttpError):
            controller.signup(user, email=user.email)

        invite_required = AppSettings.objects.get(name='Invite Required')
        invite_required.value = '1'
        invite_required.save()

        signed_user = baker.make(User)
        utils.create_social_auth(signed_user)
        signed_account = baker.make(Account, user=signed_user, is_verified=True)
        Invite.objects.create(owned_by=signed_account, email=user.email)

        with self.assertRaises(HttpError):
            controller.signup(user, email=user.email)

        user.is_alpha = True
        user.save()
        user.refresh_from_db()
        controller.signup(user, email=user.email)

    def test_auth_on_beta(self):
        user = baker.make(User)
        utils.create_social_auth(user)
        baker.make(Account, user=user, is_verified=True)
        controller.auth(user)

        beta_required = AppSettings.objects.get(name='Beta Required')
        beta_required.value = '1'
        beta_required.save()

        with self.assertRaises(HttpError):
            controller.auth(user)

        baker.make(BetaUser, email=user.email)
        controller.auth(user)

    def test_auth_on_alpha(self):
        user = baker.make(User)
        utils.create_social_auth(user)
        baker.make(Account, user=user, is_verified=True)
        controller.auth(user)

        alpha_required = AppSettings.objects.get(name='Alpha Required')
        alpha_required.value = '1'
        alpha_required.save()

        with self.assertRaises(HttpError):
            controller.auth(user)

        user.is_alpha = True
        user.save()
        user.refresh_from_db()
        controller.auth(user)

    @mock.patch('accounts.api.controller.tasks.send_welcome_email.delay')
    @mock.patch('store.models.repopulate_user_store.apply_async')
    def test_verify_account(self, mock_user_store_task, mock_welcome_email):
        self.assertFalse(hasattr(self.user, 'userstore'))
        controller.verify_account(self.user, self.user.account.verification_token)
        self.user.refresh_from_db()
        self.assertTrue(self.user.account.is_verified)
        self.assertIsNone(self.user.auth.sessions)
        self.assertTrue(hasattr(self.user, 'userstore'))
        self.assertIsNotNone(self.user.userstore)

        mock_welcome_email.assert_called_once_with(self.user.email)

    def test_verify_account_already_verified(self):
        self.user.account.is_verified = True
        self.user.account.save()
        with self.assertRaises(HttpError):
            controller.verify_account(self.user, self.user.account.verification_token)

    @mock.patch('accounts.utils.send_inactivation_mail')
    def test_inactivate(self, mocker):
        self.user.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)
        self.assertTrue(self.user.is_active)
        controller.inactivate(self.user)
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.date_inactivation)

        mocker.assert_called_once()
        mocker.assert_called_once_with(self.user.email)

    @mock.patch('accounts.utils.send_inactivation_mail')
    @mock.patch.object(
        controller.Account,
        'pre_match',
        new_callable=mock.PropertyMock,
    )
    @mock.patch('accounts.models.Account.get_match')
    @mock.patch.object(
        controller.Lobby,
        'queue',
        new_callable=mock.PropertyMock,
    )
    def test_inactivate_in_match_pre_match_queue(
        self,
        lobby_mock,
        match_mock,
        pre_match_mock,
        mocker,
    ):
        self.user.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)
        self.assertTrue(self.user.is_active)

        match_mock.return_value = True
        with self.assertRaises(HttpError):
            controller.inactivate(self.user)
        match_mock.return_value = False

        pre_match_mock.return_value = True
        with self.assertRaises(HttpError):
            controller.inactivate(self.user)
        pre_match_mock.return_value = False

        lobby_mock.return_value = True
        with self.assertRaises(HttpError):
            controller.inactivate(self.user)
        lobby_mock.return_value = False

        controller.inactivate(self.user)
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.date_inactivation)

    @mock.patch('accounts.api.controller.handle_player_move')
    @mock.patch('accounts.api.controller.websocket.ws_update_user')
    @mock.patch('accounts.api.controller.utils.send_verify_account_mail')
    def test_update_email(self, mock_send_email, mock_update_user, mock_player_move):
        self.user.account.is_verified = True
        self.user.account.save()
        self.user.add_session()
        Lobby.create(self.user.id)
        controller.update_email(self.user, 'new@email.com')
        self.assertFalse(self.user.account.is_verified)
        self.assertEqual(self.user.email, 'new@email.com')

        mock_update_user.assert_called_once()
        mock_send_email.assert_called_once()
        mock_send_email.assert_called_once_with(
            self.user.email,
            self.user.steam_user.username,
            self.user.account.verification_token,
        )
        mock_player_move.assert_called_once_with(
            self.user,
            self.user.id,
            delete_lobby=True,
        )

    @mock.patch(
        'accounts.utils.send_verify_account_mail',
        return_value=True,
    )
    def test_update_email_should_send_verification_email(self, mocker):
        self.user.account.is_verified = True
        self.user.account.save()
        self.user.add_session()
        Lobby.create(self.user.id)
        controller.update_email(self.user, 'new@email.com')
        mocker.assert_called_once()

    @mock.patch('accounts.api.controller.cache.delete')
    @mock.patch('accounts.api.controller.websocket.ws_user_logout')
    def test_logout(self, mock_user_logout, mock_cache_delete):
        self.user.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)
        self.assertEqual(self.user.account.lobby.id, self.user.id)

        controller.logout(self.user)

        self.assertIsNone(self.user.account.lobby)
        self.assertFalse(self.user.is_online)
        mock_cache_delete.assert_called_with(f'__friendlist:user:{self.user.id}')
        mock_user_logout.assert_called_once()

    def test_logout_other_lobby(self):
        self.user.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)

        another_user = User.objects.create_user(
            "hulk@avengers.com",
            "hulkbuster",
        )
        utils.create_social_auth(another_user)
        baker.make(Account, user=another_user)
        another_user.add_session()
        another_user.account.is_verified = True
        another_user.account.save()
        lobby_2 = Lobby.create(another_user.id)
        lobby_2.invite(another_user.id, self.user.id)
        Lobby.move(self.user.id, lobby_2.id)

        self.assertEqual(self.user.account.lobby.id, lobby_2.id)

        controller.logout(self.user)

        self.assertIsNone(self.user.account.lobby)
        self.assertFalse(self.user.is_online)

    def test_delete_account(self):
        self.user.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        user_id = self.user.id

        Lobby.create(self.user.id)
        controller.delete_account(self.user)

        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(pk=user_id)

    @mock.patch.object(
        controller.Account,
        'pre_match',
        new_callable=mock.PropertyMock,
    )
    @mock.patch('accounts.models.Account.get_match')
    @mock.patch.object(
        controller.Lobby,
        'queue',
        new_callable=mock.PropertyMock,
    )
    def test_delete_account_in_match_pre_match_queue(
        self,
        lobby_mock,
        match_mock,
        pre_match_mock,
    ):
        user_id = self.user.id
        self.user.add_session()
        self.user.account.is_verified = True
        self.user.account.save()
        Lobby.create(self.user.id)
        self.assertTrue(self.user.is_active)

        match_mock.return_value = True
        with self.assertRaises(HttpError):
            controller.delete_account(self.user)
        match_mock.return_value = False

        pre_match_mock.return_value = True
        with self.assertRaises(HttpError):
            controller.delete_account(self.user)
        pre_match_mock.return_value = False

        lobby_mock.return_value = True
        with self.assertRaises(HttpError):
            controller.delete_account(self.user)
        lobby_mock.return_value = False

        controller.delete_account(self.user)
        with self.assertRaises(ObjectDoesNotExist):
            User.objects.get(pk=user_id)


class AccountsControllerVerifiedPlayersTestCase(mixins.VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.add_session()
        self.user_2.add_session()
        self.user_3.add_session()
        self.user_4.add_session()
        self.user_5.add_session()
        self.user_6.add_session()

    @mock.patch('accounts.api.controller.ws_expire_player_invites')
    @mock.patch('accounts.api.controller.handle_player_move')
    def test_logout_lobby_owner(
        self,
        mock_expire_player_invites,
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
        mock_player_move.assert_called_once()

    def test_user_matches(self):
        self.assertCountEqual(
            self.user_1.account.get_matches_played(),
            controller.user_matches(self.user_1.id),
        )

        with self.assertRaises(Http404):
            controller.user_matches(597865)

    def test_auth(self):
        self.user_1.auth.remove_session()
        self.user_1.logout()

        controller.auth(self.user_1)
        self.assertIsNotNone(self.user_1.auth.sessions)
        self.assertIsNotNone(self.user_1.account.lobby)

    def test_auth_unverified(self):
        self.user_1.account.is_verified = False
        self.user_1.account.save()
        self.user_1.refresh_from_db()

        self.user_1.auth.remove_session()
        self.user_1.logout()

        controller.auth(self.user_1)
        self.assertIsNone(self.user_1.auth.sessions)
        self.assertIsNone(self.user_1.account.lobby)

    def test_auth_no_account(self):
        self.user_1.account.delete()
        self.user_1.refresh_from_db()

        self.user_1.auth.remove_session()
        self.user_1.logout()

        controller.auth(self.user_1)
        self.assertIsNone(self.user_1.auth.sessions)
        self.assertFalse(hasattr(self.user_1, 'account'))

    def test_auth_with_session(self):
        controller.auth(self.user_1)
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

    @mock.patch('accounts.api.controller.tasks.send_invite_mail.delay')
    def test_send_invite(self, mock_send_email):
        controller.send_invite(self.user_1, 'test@email.com')
        self.assertTrue(
            self.user_1.account.invite_set.filter(email='test@email.com').exists()
        )
        mock_send_email.assert_called_once()

    def test_logout_no_account(self):
        user = baker.make(User)
        controller.logout(user)
