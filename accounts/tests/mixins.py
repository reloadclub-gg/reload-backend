import random

from django.contrib.auth import get_user_model
from model_bakery import baker

from ..models import Account
from ..utils import create_social_auth

User = get_user_model()


class UserOneMixin:
    def setUp(self):
        super().setUp()

        self.user = User.objects.create_user(
            "spiderman@avengers.com",
            "mrstark",
        )
        self.social_auth = create_social_auth(self.user)


class AccountOneMixin(UserOneMixin):
    def setUp(self):
        super().setUp()
        self.account = baker.make(Account, user=self.user)


class VerifiedAccountMixin(UserOneMixin):
    def setUp(self):
        super().setUp()
        self.account = baker.make(Account, user=self.user, is_verified=True)


class UserWithFriendsMixin(VerifiedAccountMixin):
    def setUp(self):
        super().setUp()

        self.friend1 = baker.make(User)
        create_social_auth(self.friend1)
        baker.make(Account, user=self.friend1, is_verified=True)

        self.friend2 = baker.make(User)
        create_social_auth(self.friend2)
        baker.make(Account, user=self.friend2, is_verified=True)


class Random3HundredUsersMixin:
    def setUp(self):
        super().setUp()

        for index in range(0, 300):
            user = baker.make(User)
            create_social_auth(user)
            setattr(
                self,
                f'user{index+1}',
                user,
            )

        self.users = User.objects.all()


class Random3HundredsAccountsMixin(Random3HundredUsersMixin):
    def setUp(self):
        super().setUp()

        for user in self.users.all().order_by('id')[:150]:
            setattr(
                self,
                f'account{user.id}',
                baker.make(Account, user=user, is_verified=True),
            )

        for user in self.users.order_by('id')[150:]:
            setattr(
                self,
                f'account{user.id}',
                baker.make(Account, user=user, is_verified=False),
            )

    def random_verified(self, exclude=[]):
        users = self.users.order_by('id')[:150]
        return random.choice([user for user in users if user.id not in exclude])

    def random_unverified(self, exclude=[]):
        users = self.users.order_by('id')[150:]
        return random.choice([user for user in users if user.id not in exclude])


class VerifiedAccountsMixin:
    def setUp(self):
        super().setUp()

        self.user_1 = baker.make(User, email='user_1@example.com')
        create_social_auth(self.user_1)
        baker.make(Account, user=self.user_1, is_verified=True)

        self.user_2 = baker.make(User, email='user_2@example.com')
        create_social_auth(self.user_2)
        baker.make(Account, user=self.user_2, is_verified=True)

        self.user_3 = baker.make(User, email='user_3@example.com')
        create_social_auth(self.user_3)
        baker.make(Account, user=self.user_3, is_verified=True)

        self.user_4 = baker.make(User, email='user_4@example.com')
        create_social_auth(self.user_4)
        baker.make(Account, user=self.user_4, is_verified=True)

        self.user_5 = baker.make(User, email='user_5@example.com')
        create_social_auth(self.user_5)
        baker.make(Account, user=self.user_5, is_verified=True)

        self.user_6 = baker.make(User, email='user_6@example.com')
        create_social_auth(self.user_6)
        baker.make(Account, user=self.user_6, is_verified=True)

        self.user_7 = baker.make(User, email='user_7@example.com')
        create_social_auth(self.user_7)
        baker.make(Account, user=self.user_7, is_verified=True)

        self.user_8 = baker.make(User, email='user_8@example.com')
        create_social_auth(self.user_8)
        baker.make(Account, user=self.user_8, is_verified=True)

        self.user_9 = baker.make(User, email='user_9@example.com')
        create_social_auth(self.user_9)
        baker.make(Account, user=self.user_9, is_verified=True)

        self.user_10 = baker.make(User, email='user_10@example.com')
        create_social_auth(self.user_10)
        baker.make(Account, user=self.user_10, is_verified=True)

        self.user_11 = baker.make(User, email='user_11@example.com')
        create_social_auth(self.user_11)
        baker.make(Account, user=self.user_11, is_verified=True)

        self.user_12 = baker.make(User, email='user_12@example.com')
        create_social_auth(self.user_12)
        baker.make(Account, user=self.user_12, is_verified=True)

        self.user_13 = baker.make(User, email='user_13@example.com')
        create_social_auth(self.user_13)
        baker.make(Account, user=self.user_13, is_verified=True)

        self.user_14 = baker.make(User, email='user_14@example.com')
        create_social_auth(self.user_14)
        baker.make(Account, user=self.user_14, is_verified=True)

        self.user_15 = baker.make(User, email='user_15@example.com')
        create_social_auth(self.user_15)
        baker.make(Account, user=self.user_15, is_verified=True)

        self.online_noaccount_user = baker.make(
            User, email='online_noaccount_user@example.com'
        )
        create_social_auth(self.online_noaccount_user)

        self.offline_noaccount_user = baker.make(User)
        create_social_auth(self.offline_noaccount_user)

        self.online_unverified_user = baker.make(
            User, email='online_unverified_user@example.com'
        )
        create_social_auth(self.online_unverified_user)
        baker.make(Account, user=self.online_unverified_user, is_verified=False)

        self.offline_unverified_user = baker.make(User)
        create_social_auth(self.offline_unverified_user)
        baker.make(Account, user=self.offline_unverified_user, is_verified=False)

        self.offline_verified_user = baker.make(User)
        create_social_auth(self.offline_verified_user)
        baker.make(Account, user=self.offline_verified_user, is_verified=True)
