from core.tests import TestCase

from ..api import schemas
from ..models import Lobby
from . import mixins


class LobbySchemaTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

    def test_lobby_schema_as_dict(self):
        lobby = Lobby.create(self.user_1.id)
        payload = schemas.LobbySchema.from_orm(lobby).dict()

        expected_payload = {
            'id': self.user_1.id,
            'owner_id': self.user_1.id,
            'lobby_type': 'competitive',
            'mode': 5,
            'max_players': 5,
            'players_ids': [self.user_1.id],
            'players': [schemas.LobbyPlayerSchema.from_orm(self.user_1).dict()],
            'players_count': 1,
            'non_owners_ids': [],
            'is_public': False,
            'invites': [],
            'invited_players_ids': [],
            'overall': 0,
            'seats': 4,
            'queue': None,
            'queue_time': None,
        }

        self.assertDictEqual(payload, expected_payload)

    def test_lobby_schema_with_two_player_as_dict(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        payload = schemas.LobbySchema.from_orm(lobby_1).dict()

        expected_payload = {
            'id': self.user_1.id,
            'owner_id': self.user_1.id,
            'lobby_type': 'competitive',
            'mode': 5,
            'max_players': 5,
            'players_ids': [self.user_1.id, self.user_2.id],
            'players': [
                schemas.LobbyPlayerSchema.from_orm(self.user_1).dict(),
                schemas.LobbyPlayerSchema.from_orm(self.user_2).dict(),
            ],
            'players_count': 2,
            'non_owners_ids': [self.user_2.id],
            'is_public': False,
            'invites': [],
            'invited_players_ids': [],
            'overall': 0,
            'seats': 3,
            'queue': None,
            'queue_time': None,
        }

        self.assertDictEqual(payload, expected_payload)
