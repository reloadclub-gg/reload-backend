from django.contrib.auth import get_user_model

from lobbies.tests.mixins import LobbiesMixin

from ..models import Team

User = get_user_model()


class TeamsMixin(LobbiesMixin):
    def setUp(self):
        super().setUp()

        self.lobby1.update_queue('start')
        self.lobby2.update_queue('start')
        self.lobby3.update_queue('start')
        self.lobby4.update_queue('start')
        self.lobby5.update_queue('start')

        self.team1 = Team.create(
            [
                self.lobby1.id,
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
            ]
        )

        self.lobby6.update_queue('start')
        self.lobby7.update_queue('start')
        self.lobby8.update_queue('start')
        self.lobby9.update_queue('start')
        self.lobby10.update_queue('start')

        self.team2 = Team.create(
            [
                self.lobby6.id,
                self.lobby7.id,
                self.lobby8.id,
                self.lobby9.id,
                self.lobby10.id,
            ]
        )

        self.lobby16.update_queue('start')
        self.lobby17.update_queue('start')
        self.lobby18.update_queue('start')
        self.lobby19.update_queue('start')
        self.lobby20.update_queue('start')
        self.team3 = Team.create(
            [
                self.lobby16.id,
                self.lobby17.id,
                self.lobby18.id,
                self.lobby19.id,
                self.lobby20.id,
            ]
        )

        self.lobby21.update_queue('start')
        self.lobby22.update_queue('start')
        self.lobby23.update_queue('start')
        self.lobby24.update_queue('start')
        self.lobby25.update_queue('start')
        self.team4 = Team.create(
            [
                self.lobby21.id,
                self.lobby22.id,
                self.lobby23.id,
                self.lobby24.id,
                self.lobby25.id,
            ]
        )
