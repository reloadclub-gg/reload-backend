from django.contrib.auth import get_user_model

from lobbies.tests.mixins import LobbiesMixin

from ..models import Team

User = get_user_model()


class TeamsMixin(LobbiesMixin):
    def setUp(self):
        super().setUp()

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
        self.team3 = Team.create(
            [
                self.lobby16.id,
                self.lobby17.id,
                self.lobby18.id,
                self.lobby19.id,
                self.lobby20.id,
            ]
        )
        self.team4 = Team.create(
            [
                self.lobby21.id,
                self.lobby22.id,
                self.lobby23.id,
                self.lobby24.id,
                self.lobby25.id,
            ]
        )
