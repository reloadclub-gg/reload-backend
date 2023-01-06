from core.tests import TestCase
from . import mixins
from ..api import schemas
from ..models import Lobby


class LobbySchemaTestCase(mixins.SomePlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.online_verified_user_1.auth.add_session()
        self.online_verified_user_2.auth.add_session()

    def test_lobby_schema_as_dict(self):
        lobby = Lobby.create(self.online_verified_user_1.id)
        payload = schemas.LobbySchema.from_orm(lobby).dict()

        expected_payload = {
            'id': lobby.id,
            'owner_id': lobby.owner_id,
            'players_ids': [self.online_verified_user_1.id],
        }

        self.assertDictEqual(payload, expected_payload)

    def test_lobby_schema_with_two_player_as_dict(self):
        lobby_1 = Lobby.create(self.online_verified_user_1.id)
        lobby_2 = Lobby.create(self.online_verified_user_2.id)
        lobby_1.invite(lobby_2.id)
        Lobby.move(lobby_2.id, lobby_1.id)
        payload = schemas.LobbySchema.from_orm(lobby_1).dict()

        expected_payload = {
            'id': lobby_1.id,
            'owner_id': lobby_1.owner_id,
            'players_ids': [
                self.online_verified_user_1.id,
                self.online_verified_user_2.id,
            ],
        }

        self.assertDictEqual(payload, expected_payload)
