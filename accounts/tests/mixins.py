import random

from model_bakery import baker

from django.contrib.auth import get_user_model

from ..models import Account
from ..utils import create_social_auth

User = get_user_model()


class UserOneMixin:
    @classmethod
    def setUpTestData(cls):
        super(UserOneMixin, cls).setUpTestData()

        cls.user = User.objects.create_user(
            "spiderman@avengers.com",
            "mrstark",
        )
        cls.social_auth = create_social_auth(cls.user)


class AccountOneMixin(UserOneMixin):
    @classmethod
    def setUpTestData(cls):
        super(AccountOneMixin, cls).setUpTestData()
        cls.account = baker.make(Account, user=cls.user)


class UserWithFriendsMixin(AccountOneMixin):
    @classmethod
    def setUpTestData(cls):
        super(UserWithFriendsMixin, cls).setUpTestData()

        cls.friend1 = baker.make(User)
        create_social_auth(cls.friend1)
        baker.make(Account, user=cls.friend1, is_verified=True)

        cls.friend2 = baker.make(User)
        create_social_auth(cls.friend2)
        baker.make(Account, user=cls.friend2, is_verified=True)


class Random3HundredUsersMixin:
    @classmethod
    def setUpTestData(cls):
        super(Random3HundredUsersMixin, cls).setUpTestData()

        for index in range(0, 300):
            user = baker.make(User)
            create_social_auth(user)
            setattr(
                cls,
                f'user{index+1}',
                user,
            )

        cls.users = User.objects.all()


class Random3HundredsAccountsMixin(Random3HundredUsersMixin):
    @classmethod
    def setUpTestData(cls):
        super(Random3HundredsAccountsMixin, cls).setUpTestData()

        for user in cls.users.all().order_by('id')[:150]:
            setattr(
                cls,
                f'account{user.id}',
                baker.make(Account, user=user, is_verified=True),
            )

        for user in cls.users.order_by('id')[150:]:
            setattr(
                cls,
                f'account{user.id}',
                baker.make(Account, user=user, is_verified=False),
            )

    def random_verified(self, exclude=[]):
        users = self.users.order_by('id')[:150]
        return random.choice([user for user in users if user.id not in exclude])

    def random_unverified(self, exclude=[]):
        users = self.users.order_by('id')[150:]
        return random.choice([user for user in users if user.id not in exclude])
