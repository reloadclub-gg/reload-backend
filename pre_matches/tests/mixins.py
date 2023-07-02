from django.contrib.auth import get_user_model

from accounts.tests.mixins import VerifiedAccountsMixin
from lobbies.models import Lobby

from ..models import Team

User = get_user_model()


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
