from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase
from steam import Steam

from ..api import schemas
from ..models import Lobby


class LobbySchemaTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

    def test_lobby_player_schema(self):
        Lobby.create(self.user_1.id)
        payload = schemas.LobbyPlayerSchema.from_orm(self.user_1).dict()

        expected_payload = {
            'user_id': self.user_1.id,
            'username': self.user_1.account.username,
            'steamid': self.user_1.account.steamid,
            'level': self.user_1.account.level,
            'level_points': self.user_1.account.level_points,
            'highest_level': self.user_1.account.highest_level,
            'avatar': {
                'small': Steam.build_avatar_url(self.user_1.steam_user.avatarhash),
                'medium': Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'medium'
                ),
                'large': Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'full'
                ),
            },
            'matches_played': len(self.user_1.account.matches_played),
            'matches_won': self.user_1.account.matches_won,
            'highest_win_streak': self.user_1.account.highest_win_streak,
            'latest_matches_results': self.user_1.account.get_latest_matches_results(),
            'most_kills_in_a_match': self.user_1.account.get_most_stat_in_match(
                'kills'
            ),
            'most_damage_in_a_match': self.user_1.account.get_most_stat_in_match(
                'damage'
            ),
            'steam_url': self.user_1.steam_user.profileurl,
            'status': self.user_1.status,
            'lobby_id': self.user_1.account.lobby.id,
        }
        self.assertDictEqual(payload, expected_payload)

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
            'restriction_countdown': None,
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
            'restriction_countdown': None,
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
            'from_player': schemas.LobbyPlayerSchema.from_orm(self.user_1).dict(),
            'to_player': schemas.LobbyPlayerSchema.from_orm(self.user_2).dict(),
            'create_date': invite.create_date.isoformat(),
        }

        self.assertDictEqual(payload, expected_payload)
