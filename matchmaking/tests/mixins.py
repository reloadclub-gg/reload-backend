from django.contrib.auth import get_user_model
from model_bakery import baker

from accounts.models import Account
from accounts.utils import create_social_auth
from matchmaking.models import Lobby, Team

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

        cls.user_7 = baker.make(User, email='user_7@example.com')
        create_social_auth(cls.user_7)
        baker.make(Account, user=cls.user_7, is_verified=True)

        cls.user_8 = baker.make(User, email='user_8@example.com')
        create_social_auth(cls.user_8)
        baker.make(Account, user=cls.user_8, is_verified=True)

        cls.user_9 = baker.make(User, email='user_9@example.com')
        create_social_auth(cls.user_9)
        baker.make(Account, user=cls.user_9, is_verified=True)

        cls.user_10 = baker.make(User, email='user_10@example.com')
        create_social_auth(cls.user_10)
        baker.make(Account, user=cls.user_10, is_verified=True)

        cls.user_11 = baker.make(User, email='user_11@example.com')
        create_social_auth(cls.user_11)
        baker.make(Account, user=cls.user_11, is_verified=True)

        cls.user_12 = baker.make(User, email='user_12@example.com')
        create_social_auth(cls.user_12)
        baker.make(Account, user=cls.user_12, is_verified=True)

        cls.user_13 = baker.make(User, email='user_13@example.com')
        create_social_auth(cls.user_13)
        baker.make(Account, user=cls.user_13, is_verified=True)

        cls.user_14 = baker.make(User, email='user_14@example.com')
        create_social_auth(cls.user_14)
        baker.make(Account, user=cls.user_14, is_verified=True)

        cls.user_15 = baker.make(User, email='user_15@example.com')
        create_social_auth(cls.user_15)
        baker.make(Account, user=cls.user_15, is_verified=True)

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


class TeamsMixin(VerifiedPlayersMixin):
    @classmethod
    def setUpTestData(cls):
        super(TeamsMixin, cls).setUpTestData()

        cls.user_1.auth.add_session()
        cls.user_2.auth.add_session()
        cls.user_3.auth.add_session()
        cls.user_4.auth.add_session()
        cls.user_5.auth.add_session()
        cls.user_6.auth.add_session()
        cls.user_7.auth.add_session()
        cls.user_8.auth.add_session()
        cls.user_9.auth.add_session()
        cls.user_10.auth.add_session()
        cls.user_11.auth.add_session()
        cls.user_12.auth.add_session()
        cls.user_13.auth.add_session()
        cls.user_14.auth.add_session()
        cls.user_15.auth.add_session()

        cls.user_1.auth.create_token()
        cls.user_2.auth.create_token()
        cls.user_3.auth.create_token()
        cls.user_4.auth.create_token()
        cls.user_5.auth.create_token()
        cls.user_6.auth.create_token()
        cls.user_7.auth.create_token()
        cls.user_8.auth.create_token()
        cls.user_9.auth.create_token()
        cls.user_10.auth.create_token()
        cls.user_11.auth.create_token()
        cls.user_12.auth.create_token()
        cls.user_13.auth.create_token()
        cls.user_14.auth.create_token()
        cls.user_15.auth.create_token()

        cls.lobby1 = Lobby.create(owner_id=cls.user_1.id)
        cls.lobby2 = Lobby.create(owner_id=cls.user_2.id)
        cls.lobby3 = Lobby.create(owner_id=cls.user_3.id)
        cls.lobby4 = Lobby.create(owner_id=cls.user_4.id)
        cls.lobby5 = Lobby.create(owner_id=cls.user_5.id)
        cls.lobby6 = Lobby.create(owner_id=cls.user_6.id)
        cls.lobby7 = Lobby.create(owner_id=cls.user_7.id)
        cls.lobby8 = Lobby.create(owner_id=cls.user_8.id)
        cls.lobby9 = Lobby.create(owner_id=cls.user_9.id)
        cls.lobby10 = Lobby.create(owner_id=cls.user_10.id)
        cls.lobby11 = Lobby.create(owner_id=cls.user_11.id)
        cls.lobby12 = Lobby.create(owner_id=cls.user_12.id)
        cls.lobby13 = Lobby.create(owner_id=cls.user_13.id)
        cls.lobby14 = Lobby.create(owner_id=cls.user_14.id)
        cls.lobby15 = Lobby.create(owner_id=cls.user_15.id)

        cls.team1 = Team.create(
            [
                cls.lobby1.id,
                cls.lobby2.id,
                cls.lobby3.id,
                cls.lobby4.id,
                cls.lobby5.id,
            ]
        )
        cls.team2 = Team.create(
            [
                cls.lobby6.id,
                cls.lobby7.id,
                cls.lobby8.id,
                cls.lobby9.id,
                cls.lobby10.id,
            ]
        )
