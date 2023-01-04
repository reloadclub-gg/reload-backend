from model_bakery import baker

from django.contrib.auth import get_user_model

from accounts.models import Account
from accounts.utils import create_social_auth

User = get_user_model()


class SomePlayersMixin:
    @classmethod
    def setUpTestData(cls):
        super(SomePlayersMixin, cls).setUpTestData()

        cls.online_verified_user_1 = baker.make(
            User, email='online_verified_user_1@example.com'
        )
        create_social_auth(cls.online_verified_user_1)
        baker.make(Account, user=cls.online_verified_user_1, is_verified=True)

        cls.online_verified_user_2 = baker.make(
            User, email='online_verified_user_2@example.com'
        )
        create_social_auth(cls.online_verified_user_2)
        baker.make(Account, user=cls.online_verified_user_2, is_verified=True)

        cls.online_verified_user_3 = baker.make(
            User, email='online_verified_user_3@example.com'
        )
        create_social_auth(cls.online_verified_user_3)
        baker.make(Account, user=cls.online_verified_user_3, is_verified=True)

        cls.online_verified_user_4 = baker.make(
            User, email='online_verified_user_4@example.com'
        )
        create_social_auth(cls.online_verified_user_4)
        baker.make(Account, user=cls.online_verified_user_4, is_verified=True)

        cls.online_verified_user_5 = baker.make(
            User, email='online_verified_user_5@example.com'
        )
        create_social_auth(cls.online_verified_user_5)
        baker.make(Account, user=cls.online_verified_user_5, is_verified=True)

        cls.online_verified_user_6 = baker.make(
            User, email='online_verified_user_6@example.com'
        )
        create_social_auth(cls.online_verified_user_6)
        baker.make(Account, user=cls.online_verified_user_6, is_verified=True)

        cls.online_noaccount_user = baker.make(
            User, email='online_noaccount_user@example.com'
        )
        create_social_auth(cls.online_noaccount_user)

        cls.offline_noaccount_user = baker.make(User)
        create_social_auth(cls.offline_noaccount_user)

        cls.online_unverified_user = baker.make(
            User, email='online_unverified_user@example.com'
        )
        create_social_auth(cls.online_unverified_user)
        baker.make(Account, user=cls.online_unverified_user, is_verified=False)

        cls.offline_unverified_user = baker.make(User)
        create_social_auth(cls.offline_unverified_user)
        baker.make(Account, user=cls.offline_unverified_user, is_verified=False)

        cls.offline_verified_user = baker.make(User)
        create_social_auth(cls.offline_verified_user)
        baker.make(Account, user=cls.offline_verified_user, is_verified=True)


class VerifiedPlayersMixin:
    @classmethod
    def setUpTestData(cls):
        super(VerifiedPlayersMixin, cls).setUpTestData()

        cls.user_1 = baker.make(User, email='user_1@example.com')
        create_social_auth(cls.user_1)
        baker.make(Account, user=cls.user_1, is_verified=True)

        cls.user_2 = baker.make(User, email='user_2@example.com')
        create_social_auth(cls.user_2)
        baker.make(Account, user=cls.user_2, is_verified=True)

        cls.user_3 = baker.make(User, email='user_3@example.com')
        create_social_auth(cls.user_3)
        baker.make(Account, user=cls.user_3, is_verified=True)

        cls.user_4 = baker.make(User, email='user_4@example.com')
        create_social_auth(cls.user_4)
        baker.make(Account, user=cls.user_4, is_verified=True)

        cls.user_5 = baker.make(User, email='user_5@example.com')
        create_social_auth(cls.user_5)
        baker.make(Account, user=cls.user_5, is_verified=True)

        cls.user_6 = baker.make(User, email='user_6@example.com')
        create_social_auth(cls.user_6)
        baker.make(Account, user=cls.user_6, is_verified=True)

        cls.online_noaccount_user = baker.make(
            User, email='online_noaccount_user@example.com'
        )
        create_social_auth(cls.online_noaccount_user)

        cls.offline_noaccount_user = baker.make(User)
        create_social_auth(cls.offline_noaccount_user)

        cls.online_unverified_user = baker.make(
            User, email='online_unverified_user@example.com'
        )
        create_social_auth(cls.online_unverified_user)
        baker.make(Account, user=cls.online_unverified_user, is_verified=False)

        cls.offline_unverified_user = baker.make(User)
        create_social_auth(cls.offline_unverified_user)
        baker.make(Account, user=cls.offline_unverified_user, is_verified=False)

        cls.offline_verified_user = baker.make(User)
        create_social_auth(cls.offline_verified_user)
        baker.make(Account, user=cls.offline_verified_user, is_verified=True)
