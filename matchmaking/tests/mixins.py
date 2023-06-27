from django.contrib.auth import get_user_model
from model_bakery import baker

from accounts.models import Account
from accounts.utils import create_social_auth
from lobbies.models import Lobby
from matchmaking.models import Team

User = get_user_model()


class SomePlayersMixin:
    def setUp(self):
        super().setUp()

        self.online_verified_user_1 = baker.make(
            User, email='online_verified_user_1@example.com'
        )
        create_social_auth(self.online_verified_user_1)
        baker.make(Account, user=self.online_verified_user_1, is_verified=True)

        self.online_verified_user_2 = baker.make(
            User, email='online_verified_user_2@example.com'
        )
        create_social_auth(self.online_verified_user_2)
        baker.make(Account, user=self.online_verified_user_2, is_verified=True)

        self.online_verified_user_3 = baker.make(
            User, email='online_verified_user_3@example.com'
        )
        create_social_auth(self.online_verified_user_3)
        baker.make(Account, user=self.online_verified_user_3, is_verified=True)

        self.online_verified_user_4 = baker.make(
            User, email='online_verified_user_4@example.com'
        )
        create_social_auth(self.online_verified_user_4)
        baker.make(Account, user=self.online_verified_user_4, is_verified=True)

        self.online_verified_user_5 = baker.make(
            User, email='online_verified_user_5@example.com'
        )
        create_social_auth(self.online_verified_user_5)
        baker.make(Account, user=self.online_verified_user_5, is_verified=True)

        self.online_verified_user_6 = baker.make(
            User, email='online_verified_user_6@example.com'
        )
        create_social_auth(self.online_verified_user_6)
        baker.make(Account, user=self.online_verified_user_6, is_verified=True)

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


class TeamsMixin(VerifiedAccountsMixin):
    def setUp(self):
        super().setUp()

        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()
        self.user_7.auth.add_session()
        self.user_8.auth.add_session()
        self.user_9.auth.add_session()
        self.user_10.auth.add_session()
        self.user_11.auth.add_session()
        self.user_12.auth.add_session()
        self.user_13.auth.add_session()
        self.user_14.auth.add_session()
        self.user_15.auth.add_session()

        self.user_1.auth.create_token()
        self.user_2.auth.create_token()
        self.user_3.auth.create_token()
        self.user_4.auth.create_token()
        self.user_5.auth.create_token()
        self.user_6.auth.create_token()
        self.user_7.auth.create_token()
        self.user_8.auth.create_token()
        self.user_9.auth.create_token()
        self.user_10.auth.create_token()
        self.user_11.auth.create_token()
        self.user_12.auth.create_token()
        self.user_13.auth.create_token()
        self.user_14.auth.create_token()
        self.user_15.auth.create_token()

        self.lobby1 = Lobby.create(owner_id=self.user_1.id)
        self.lobby2 = Lobby.create(owner_id=self.user_2.id)
        self.lobby3 = Lobby.create(owner_id=self.user_3.id)
        self.lobby4 = Lobby.create(owner_id=self.user_4.id)
        self.lobby5 = Lobby.create(owner_id=self.user_5.id)
        self.lobby6 = Lobby.create(owner_id=self.user_6.id)
        self.lobby7 = Lobby.create(owner_id=self.user_7.id)
        self.lobby8 = Lobby.create(owner_id=self.user_8.id)
        self.lobby9 = Lobby.create(owner_id=self.user_9.id)
        self.lobby10 = Lobby.create(owner_id=self.user_10.id)
        self.lobby11 = Lobby.create(owner_id=self.user_11.id)
        self.lobby12 = Lobby.create(owner_id=self.user_12.id)
        self.lobby13 = Lobby.create(owner_id=self.user_13.id)
        self.lobby14 = Lobby.create(owner_id=self.user_14.id)
        self.lobby15 = Lobby.create(owner_id=self.user_15.id)

        self.team1 = Team.create(
            [
                self.lobby1.id,
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
            ]
        )
        self.team2 = Team.create(
            [
                self.lobby6.id,
                self.lobby7.id,
                self.lobby8.id,
                self.lobby9.id,
                self.lobby10.id,
            ]
        )
