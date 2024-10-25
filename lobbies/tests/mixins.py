from accounts.tests.mixins import VerifiedAccountsMixin

from ..models import Lobby


class LobbiesMixin(VerifiedAccountsMixin):
    def setUp(self):
        super().setUp()

        self.user_1.add_session()
        self.user_2.add_session()
        self.user_3.add_session()
        self.user_4.add_session()
        self.user_5.add_session()
        self.user_6.add_session()
        self.user_7.add_session()
        self.user_8.add_session()
        self.user_9.add_session()
        self.user_10.add_session()
        self.user_11.add_session()
        self.user_12.add_session()
        self.user_13.add_session()
        self.user_14.add_session()
        self.user_15.add_session()
        self.user_16.add_session()
        self.user_17.add_session()
        self.user_18.add_session()
        self.user_19.add_session()
        self.user_20.add_session()
        self.user_21.add_session()
        self.user_22.add_session()
        self.user_23.add_session()
        self.user_24.add_session()
        self.user_25.add_session()

        self.user_1.status = "online"
        self.user_1.save()
        self.user_2.status = "online"
        self.user_2.save()
        self.user_3.status = "online"
        self.user_3.save()
        self.user_4.status = "online"
        self.user_4.save()
        self.user_5.status = "online"
        self.user_5.save()
        self.user_6.status = "online"
        self.user_6.save()
        self.user_7.status = "online"
        self.user_7.save()
        self.user_8.status = "online"
        self.user_8.save()
        self.user_9.status = "online"
        self.user_9.save()
        self.user_10.status = "online"
        self.user_10.save()
        self.user_11.status = "online"
        self.user_11.save()
        self.user_12.status = "online"
        self.user_12.save()
        self.user_13.status = "online"
        self.user_13.save()
        self.user_14.status = "online"
        self.user_14.save()
        self.user_15.status = "online"
        self.user_15.save()
        self.user_16.status = "online"
        self.user_16.save()
        self.user_17.status = "online"
        self.user_17.save()
        self.user_18.status = "online"
        self.user_18.save()
        self.user_19.status = "online"
        self.user_19.save()
        self.user_20.status = "online"
        self.user_20.save()
        self.user_21.status = "online"
        self.user_21.save()
        self.user_22.status = "online"
        self.user_22.save()
        self.user_23.status = "online"
        self.user_23.save()
        self.user_24.status = "online"
        self.user_24.save()
        self.user_25.status = "online"
        self.user_25.save()

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
        self.user_16.auth.create_token()
        self.user_17.auth.create_token()
        self.user_18.auth.create_token()
        self.user_19.auth.create_token()
        self.user_20.auth.create_token()
        self.user_21.auth.create_token()
        self.user_22.auth.create_token()
        self.user_23.auth.create_token()
        self.user_24.auth.create_token()
        self.user_25.auth.create_token()

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
        self.lobby16 = Lobby.create(owner_id=self.user_16.id)
        self.lobby17 = Lobby.create(owner_id=self.user_17.id)
        self.lobby18 = Lobby.create(owner_id=self.user_18.id)
        self.lobby19 = Lobby.create(owner_id=self.user_19.id)
        self.lobby20 = Lobby.create(owner_id=self.user_20.id)
        self.lobby21 = Lobby.create(owner_id=self.user_21.id)
        self.lobby22 = Lobby.create(owner_id=self.user_22.id)
        self.lobby23 = Lobby.create(owner_id=self.user_23.id)
        self.lobby24 = Lobby.create(owner_id=self.user_24.id)
        self.lobby25 = Lobby.create(owner_id=self.user_25.id)
