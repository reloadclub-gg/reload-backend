from django.contrib.auth import get_user_model

from lobbies.tests.mixins import LobbiesMixin

from ..models import Team

User = get_user_model()


class TeamsMixin(LobbiesMixin):
    def setUp(self):
        super().setUp()

        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()
        self.lobby5.start_queue()

        self.team1 = Team.create(
            [
                self.lobby1.id,
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
            ]
        )

        self.lobby6.start_queue()
        self.lobby7.start_queue()
        self.lobby8.start_queue()
        self.lobby9.start_queue()
        self.lobby10.start_queue()

        self.team2 = Team.create(
            [
                self.lobby6.id,
                self.lobby7.id,
                self.lobby8.id,
                self.lobby9.id,
                self.lobby10.id,
            ]
        )

        self.lobby16.start_queue()
        self.lobby17.start_queue()
        self.lobby18.start_queue()
        self.lobby19.start_queue()
        self.lobby20.start_queue()
        self.team3 = Team.create(
            [
                self.lobby16.id,
                self.lobby17.id,
                self.lobby18.id,
                self.lobby19.id,
                self.lobby20.id,
            ]
        )

        self.lobby21.start_queue()
        self.lobby22.start_queue()
        self.lobby23.start_queue()
        self.lobby24.start_queue()
        self.lobby25.start_queue()
        self.team4 = Team.create(
            [
                self.lobby21.id,
                self.lobby22.id,
                self.lobby23.id,
                self.lobby24.id,
                self.lobby25.id,
            ]
        )
