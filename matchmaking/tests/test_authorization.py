from core.tests import TestCase

from ..api.authorization import is_lobby_owner, is_lobby_participant
from ..models import Lobby
from . import mixins


class AuthorizationTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

    def test_is_lobby_owner_is_true(self):
        lobby = Lobby.create(self.user_1.id)

        self.assertTrue(is_lobby_owner(self.user_1, lobby.id))

    def test_is_lobby_owner_is_false(self):
        lobby = Lobby.create(self.user_1.id)

        self.assertFalse(is_lobby_owner(self.user_2, lobby.id))

    def test_is_lobby_participant_is_true(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_1.invite(lobby_1.id, lobby_2.id)
        Lobby.move(lobby_2.id, lobby_1.id)

        self.assertTrue(is_lobby_participant(self.user_2, lobby_1.id))

    def test_is_lobby_participant_is_false(self):
        lobby = Lobby.create(self.user_1.id)

        self.assertFalse(is_lobby_participant(self.user_2, lobby.id))
