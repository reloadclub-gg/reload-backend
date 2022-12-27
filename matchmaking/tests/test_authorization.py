from core.tests import TestCase, cache
from ..models import Lobby
from ..models.lobby import LobbyException
from ..api.authorization import is_lobby_owner, is_lobby_participant
from . import mixins


class AuthorizationTestCase(mixins.SomePlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.online_verified_user_1.auth.add_session()
        self.online_verified_user_2.auth.add_session()

    def test_is_lobby_owner_is_true(self):
        lobby = Lobby.create(self.online_verified_user_1.id)

        self.assertTrue(is_lobby_owner(self.online_verified_user_1, lobby.id))

    def test_is_lobby_owner_is_false(self):
        lobby = Lobby.create(self.online_verified_user_1.id)

        self.assertFalse(is_lobby_owner(self.online_verified_user_2, lobby.id))

    def test_is_lobby_participant_is_true(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_1.invite(lobby_2.id)
        Lobby.move(lobby_2.id, lobby_1.id)

        self.assertTrue(is_lobby_participant(self.online_verified_user_2, lobby_1.id))

    def test_is_lobby_participant_is_false(self):
        lobby = Lobby.create(self.online_verified_user_1.id)

        self.assertFalse(is_lobby_participant(self.online_verified_user_2, lobby.id))
