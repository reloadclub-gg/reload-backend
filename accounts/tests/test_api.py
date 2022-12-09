from model_bakery import baker
from ninja import Schema
from ninja.errors import HttpError

from django.http.response import Http404

from core.tests import APIClient, TestCase
from . import mixins
from ..api import controller
from ..models import Account, Auth, Invite, User, UserLogin
from .. import utils


class AccountSchema(Schema):
    is_verified: bool = False


class UserNoAccountSchema(Schema):
    id: int = None


class UserSchema(Schema):
    id: int = None
    account: AccountSchema = None


class RequestSchema(Schema):
    user: UserSchema = None
    META: dict = {
        'HTTP_X_FORWARDED_FOR': '111.111.111.111'
    }


class AccountsControllerTestCase(mixins.AccountOneMixin, TestCase):

    def test_login(self):
        auth = Auth(user_id=self.user.id, force_token_create=True)
        controller.login(RequestSchema(), auth.token)
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
        user = baker.make(User)
        with self.assertRaisesRegex(HttpError, 'Must be invited'):
            controller.signup(user, email=user.email)

    def test_verify_account(self):
        controller.verify_account(self.user, self.user.account.verification_token)
        self.user.refresh_from_db()
        self.assertTrue(self.user.account.is_verified)

    def test_verify_account_already_verified(self):
        self.user.account.is_verified = True
        self.user.account.save()
        with self.assertRaises(Http404):
            controller.verify_account(self.user, self.user.account.verification_token)

    def test_inactivate(self):
        controller.inactivate(self.user)
        self.assertFalse(self.user.is_active)

    def test_change_user_email(self):
        controller.change_user_email(self.user, 'new@email.com')


class AccountsEndpointsTestCase(mixins.UserOneMixin, TestCase):

    def setUp(self):
        self.api = APIClient('/api/accounts')
        return super().setUp()

    def test_fake_signup_existent_user(self):
        with self.settings(DEBUG=True):
            r = self.api.call(
                'post',
                '/fake-signup',
                data={'email': self.user.email}
            )
            user = User.objects.get(pk=r.json().get('id'))
            self.assertIsNotNone(user)
            self.assertEqual(user.email, self.user.email)

    def test_fake_signup(self):
        with self.settings(DEBUG=True):
            r = self.api.call(
                'post',
                '/fake-signup',
                data={'email': 'test_user@email.com'}
            )
            user = User.objects.get(pk=r.json().get('id'))
            self.assertIsNotNone(user)
            self.assertEqual(user.email, 'test_user@email.com')

        r = self.api.call(
            'post',
            '/fake-signup',
            data={'email': 'test_user@email.com'}
        )
        self.assertEqual(r.status_code, 404)

    def test_signup(self):
        account = baker.make(Account, user=self.user)
        invite = baker.make(Invite, owned_by=account, email='any@email.com')
        invited_user = baker.make(User, email='')
        utils.create_social_auth(invited_user)
        invited_user.auth.create_token()

        r = self.api.call(
            'post',
            '/',
            data={'email': invite.email, 'terms': True, 'policy': True},
            token=invited_user.auth.token
        )
        invited_user.refresh_from_db()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(invited_user.email, invite.email)
        self.assertIsNotNone(invited_user.account)
        self.assertFalse(invited_user.account.is_verified)

    def test_signup_without_terms_and_policy(self):
        account = baker.make(Account, user=self.user)
        invite = baker.make(Invite, owned_by=account, email='any@email.com')
        invited_user = baker.make(User, email='')
        utils.create_social_auth(invited_user)
        invited_user.auth.create_token()

        r = self.api.call(
            'post',
            '/',
            data={'email': invite.email, 'terms': False, 'policy': False},
            token=invited_user.auth.token
        )
        self.assertEqual(r.status_code, 422)

        r = self.api.call(
            'post',
            '/',
            data={'email': invite.email, 'terms': True, 'policy': False},
            token=invited_user.auth.token
        )
        self.assertEqual(r.status_code, 422)

        r = self.api.call(
            'post',
            '/',
            data={'email': invite.email},
            token=invited_user.auth.token
        )
        self.assertEqual(r.status_code, 422)

    def test_signup_without_invite(self):
        invited_user = baker.make(User, email='')
        utils.create_social_auth(invited_user)
        invited_user.auth.create_token()

        r = self.api.call(
            'post',
            '/',
            data={'email': 'noninvited@email.com', 'terms': True, 'policy': True},
            token=invited_user.auth.token
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json().get('detail'), 'Must be invited')

    def test_signup_with_existing_account(self):
        baker.make(Account, user=self.user)
        self.user.auth.create_token()
        r = self.api.call(
            'post',
            '/',
            data={'email': 'noninvited@email.com', 'terms': True, 'policy': True},
            token=self.user.auth.token
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json().get('detail'), 'User already has an account')

    def test_signup_with_friends(self):
        account = baker.make(Account, user=self.user, is_verified=True)
        invite = baker.make(Invite, owned_by=account, email='any@email.com')
        invited_user = baker.make(User, email='')
        utils.create_social_auth(invited_user)
        invited_user.auth.create_token()

        r = self.api.call(
            'post',
            '/',
            data={'email': invite.email, 'terms': True, 'policy': True},
            token=invited_user.auth.token
        )
        invited_user.refresh_from_db()
        self.assertEqual(r.status_code, 201)
        self.assertEqual(invited_user.email, invite.email)
        self.assertIsNotNone(invited_user.account)
        self.assertFalse(invited_user.account.is_verified)

    def test_user_detail(self):
        self.user.auth.create_token()
        r = self.api.get('/auth', token=self.user.auth.token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.user.email, r.json().get('email'))

    def test_cancel_account(self):
        self.user.auth.create_token()
        r = self.api.delete('/', token=self.user.auth.token)
        self.user.refresh_from_db()
        self.assertEqual(r.status_code, 200)
        self.assertFalse(self.user.is_active)

    def test_inactive_user_access_auth_endpoint(self):
        self.user.is_active = False
        self.user.save()

        self.user.auth.create_token()
        r = self.api.get('/auth', token=self.user.auth.token)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json().get('detail'), 'Unauthorized')

    def test_account_verification(self):
        baker.make(Account, user=self.user)
        self.user.auth.create_token()
        payload = {'verification_token': self.user.account.verification_token}
        r = self.api.call('post', '/verify', data=payload, token=self.user.auth.token)
        self.user.refresh_from_db()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(self.user.account.is_verified)

    def test_account_verification_already_verified(self):
        baker.make(Account, user=self.user, is_verified=True)
        self.user.auth.create_token()
        payload = {'verification_token': self.user.account.verification_token}
        r = self.api.call('post', '/verify', data=payload, token=self.user.auth.token)
        self.assertEqual(r.status_code, 404)

    def test_account_verification_invalid_token(self):
        self.user.auth.create_token()
        payload = {'verification_token': 'any'}
        r = self.api.call('post', '/verify', data=payload, token=self.user.auth.token)
        error_msg = r.json().get('detail')[0].get('msg')
        self.assertEqual(r.status_code, 422)
        self.assertEqual(error_msg, 'field must be valid')

    def test_change_user_email(self):
        baker.make(Account, user=self.user)
        self.user.auth.create_token()
        payload = {'email': 'new@email.com'}
        response = self.api.call(
            'post', '/change-user-email', data=payload, token=self.user.auth.token
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.email, 'new@email.com')
        self.assertFalse(self.user.account.is_verified)

    def test_change_user_email_with_same_email(self):
        baker.make(Account, user=self.user)
        self.user.auth.create_token()
        payload = {'email': self.user.email}
        response = self.api.call(
            'post', '/change-user-email', data=payload, token=self.user.auth.token
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, 422)
        self.assertDictEqual(
            response.json(),
            {
                'detail': [
                    {
                        'loc': ['body', 'payload', 'email'],
                        'msg': 'field must be unique',
                        'type': 'value_error',
                    }
                ]
            },
        )
