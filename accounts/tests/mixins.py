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
