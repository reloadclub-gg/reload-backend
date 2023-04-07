from core.tests import TestCase
from steam import Steam

from ..api import schemas
from ..models import Lobby, PreMatch, PreMatchConfig
from . import mixins


class LobbySchemaTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

    def test_lobby_player_schema(self):
        Lobby.create(self.user_1.id)
        payload = schemas.LobbyPlayerSchema.from_orm(self.user_1).dict()

        expected_payload = {
            'id': self.user_1.id,
            'steamid': self.user_1.steam_user.steamid,
            'username': self.user_1.steam_user.username,
            'avatar': {
                'small': Steam.build_avatar_url(self.user_1.steam_user.avatarhash),
                'medium': Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'medium'
                ),
                'large': Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'full'
                ),
            },
            'is_online': self.user_1.is_online,
            'level': self.user_1.account.level,
            'status': self.user_1.status,
            'steam_url': self.user_1.steam_user.profileurl,
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
        }

        self.assertDictEqual(payload, expected_payload)


class PreMatchSchemaTestCase(mixins.TeamsMixin, TestCase):
    def test_pre_match_schema(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        payload = schemas.PreMatchSchema.from_orm(pre_match).dict()

        expected_payload = {
            'id': pre_match.id,
            'state': list(PreMatchConfig.STATES.keys())[
                list(PreMatchConfig.STATES.values()).index(pre_match.state)
            ],
            'countdown': pre_match.countdown,
            'players_ready_count': len(pre_match.players_ready),
            'players_total': len(pre_match.players),
            'user_ready': False,
        }
        self.assertDictEqual(payload, expected_payload)
