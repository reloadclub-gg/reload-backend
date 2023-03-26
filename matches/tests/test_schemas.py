from model_bakery import baker

from core.tests import TestCase
from matches.api import schemas
from matches.models import Match, MatchPlayer, MatchTeam
from matchmaking.tests import mixins


class MatchesSchemasTestCase(mixins.TeamsMixin, TestCase):
    def test_match_schema(self):
        match = baker.make(Match)
        baker.make(MatchTeam, match=match)
        baker.make(MatchTeam, match=match)
        payload = schemas.MatchSchema.from_orm(match).dict()

        expected_payload = {
            'id': match.id,
            'create_date': match.create_date.isoformat(),
            'start_date': match.start_date.isoformat() if match.start_date else None,
            'end_date': match.end_date.isoformat() if match.end_date else None,
            'status': match.status,
            'game_type': match.game_type,
            'game_mode': match.game_mode,
            'server_ip': match.server.ip,
            'teams': [schemas.MatchTeamSchema.from_orm(team) for team in match.teams],
            'rounds': match.rounds,
            'winner_id': match.winner.id if match.winner else None,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_player_schema(self):
        match = baker.make(Match)
        team = baker.make(MatchTeam, match=match)
        match_player = baker.make(MatchPlayer, team=team, user=self.user_1)

        payload = schemas.MatchPlayerSchema.from_orm(match_player).dict()
        expected_payload = {
            'id': match_player.id,
            'user_id': match_player.user.id,
            'team_id': match_player.team.id,
            'match_id': match_player.team.match.id,
            'kills': 0,
            'deaths': 0,
            'assists': 0,
            'damage': 0,
            'hs_kills': 0,
            'afk': 0,
            'plants': 0,
            'defuses': 0,
            'double_kills': 0,
            'triple_kills': 0,
            'quadra_kills': 0,
            'aces': 0,
            'clutch_v1': 0,
            'clutch_v2': 0,
            'clutch_v3': 0,
            'clutch_v4': 0,
            'clutch_v5': 0,
            'firstkills': 0,
            'shots_fired': 0,
            'head_shots': 0,
            'chest_shots': 0,
            'other_shots': 0,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_with_players_schema(self):
        match = baker.make(Match)
        team_a = match.matchteam_set.create(name='Team A')
        team_b = match.matchteam_set.create(name='Team B')
        baker.make(MatchPlayer, user=self.user_1, team=team_a)
        baker.make(MatchPlayer, user=self.user_2, team=team_a)
        baker.make(MatchPlayer, user=self.user_3, team=team_a)
        baker.make(MatchPlayer, user=self.user_4, team=team_a)
        baker.make(MatchPlayer, user=self.user_5, team=team_a)
        baker.make(MatchPlayer, user=self.user_6, team=team_b)
        baker.make(MatchPlayer, user=self.user_7, team=team_b)
        baker.make(MatchPlayer, user=self.user_8, team=team_b)
        baker.make(MatchPlayer, user=self.user_9, team=team_b)
        baker.make(MatchPlayer, user=self.user_10, team=team_b)

        payload = schemas.MatchSchema.from_orm(match).dict()
        expected_payload = {
            'id': match.id,
            'create_date': match.create_date.isoformat(),
            'start_date': match.start_date.isoformat() if match.start_date else None,
            'end_date': match.end_date.isoformat() if match.end_date else None,
            'status': match.status,
            'game_type': match.game_type,
            'game_mode': match.game_mode,
            'server_ip': match.server.ip,
            'teams': [schemas.MatchTeamSchema.from_orm(team) for team in match.teams],
            'rounds': match.rounds,
            'winner_id': match.winner.id if match.winner else None,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_team_schema(self):
        match = baker.make(Match)
        team = baker.make(MatchTeam, match=match)
        payload = schemas.MatchTeamSchema.from_orm(team).dict()
        expected_payload = {
            'id': team.id,
            'name': team.name,
            'score': team.score,
            'match_id': team.match.id,
            'players': [
                schemas.MatchPlayerSchema.from_orm(match_player)
                for match_player in match.players
            ],
        }
        self.assertDictEqual(payload, expected_payload)
