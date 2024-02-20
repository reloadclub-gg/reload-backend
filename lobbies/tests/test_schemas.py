from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase
from core.utils import get_full_file_path
from store.models import Item

from ..api import schemas
from ..models import Lobby


class LobbySchemaTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.add_session()
        self.user_2.add_session()

    def test_lobby_player_schema(self):
        Lobby.create(self.user_1.id)
        payload = schemas.LobbyPlayerSchema.from_orm(self.user_1.account).dict()
        player_card = self.user_1.useritem_set.filter(
            item__item_type=Item.ItemType.DECORATIVE,
            item__subtype=Item.SubType.CARD,
            in_use=True,
        ).first()

        expected_payload = {
            'user_id': self.user_1.id,
            'username': self.user_1.account.username,
            'level': self.user_1.account.level,
            'avatar': self.user_1.account.avatar_dict,
            'matches_played': self.user_1.account.get_matches_played_count(),
            'latest_matches_results': self.user_1.account.get_latest_matches_results(),
            'steam_url': self.user_1.steam_user.profileurl,
            'status': self.user_1.status,
            'card': get_full_file_path(player_card) if player_card else None,
            'friends_ids': [friend.user.id for friend in self.user_1.account.friends],
        }
        self.assertDictEqual(payload, expected_payload)

    def test_lobby_schema(self):
        lobby = Lobby.create(self.user_1.id)
        payload = schemas.LobbySchema.from_orm(lobby).dict()

        expected_payload = {
            'id': self.user_1.id,
            'owner_id': self.user_1.id,
            'players_ids': [self.user_1.id],
            'players': [schemas.LobbyPlayerSchema.from_orm(self.user_1.account).dict()],
            'invites': [],
            'invited_players_ids': [],
            'seats': 4,
            'queue': None,
            'queue_time': None,
            'restriction_countdown': None,
            'lobby_match_type': None,
            'weapon': None,
            'def_players': [],
            'atk_players': [],
            'spec_players': [],
            'map_id': None,
        }

        self.assertDictEqual(payload, expected_payload)

    def test_lobby_queued_schema(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.start_queue()
        self.user_1.refresh_from_db()
        payload = schemas.LobbySchema.from_orm(lobby).dict()

        expected_payload = {
            'id': self.user_1.id,
            'owner_id': self.user_1.id,
            'players_ids': [self.user_1.id],
            'players': [schemas.LobbyPlayerSchema.from_orm(self.user_1.account).dict()],
            'invites': [],
            'invited_players_ids': [],
            'seats': 4,
            'queue': lobby.queue.isoformat(),
            'queue_time': lobby.queue_time,
            'restriction_countdown': None,
            'lobby_match_type': None,
            'weapon': None,
            'def_players': [],
            'atk_players': [],
            'spec_players': [],
            'map_id': None,
        }

        self.assertDictEqual(payload, expected_payload)

    def test_lobby_schema_with_two_player(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        payload = schemas.LobbySchema.from_orm(lobby_1).dict()

        self.user_1.refresh_from_db()
        self.user_2.refresh_from_db()

        expected_payload = {
            'id': self.user_1.id,
            'owner_id': self.user_1.id,
            'players_ids': [self.user_1.id, self.user_2.id],
            'players': [
                schemas.LobbyPlayerSchema.from_orm(self.user_1.account).dict(),
                schemas.LobbyPlayerSchema.from_orm(self.user_2.account).dict(),
            ],
            'invites': [],
            'invited_players_ids': [],
            'seats': 3,
            'queue': None,
            'queue_time': None,
            'restriction_countdown': None,
            'lobby_match_type': None,
            'weapon': None,
            'def_players': [],
            'atk_players': [],
            'spec_players': [],
            'map_id': None,
        }

        self.assertDictEqual(payload, expected_payload)

    def test_lobby_invite_schema(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        invite = lobby_1.invite(self.user_1.id, self.user_2.id)
        payload = schemas.LobbyInviteSchema.from_orm(invite).dict()

        expected_payload = {
            'id': f'{self.user_1.id}:{self.user_2.id}',
            'lobby_id': lobby_1.id,
            'lobby': schemas.LobbySchema.from_orm(lobby_1).dict(),
            'from_player': schemas.LobbyPlayerSchema.from_orm(
                self.user_1.account
            ).dict(),
            'to_player': schemas.LobbyPlayerSchema.from_orm(self.user_2.account).dict(),
            'create_date': invite.create_date.isoformat(),
        }

        self.assertDictEqual(payload, expected_payload)
