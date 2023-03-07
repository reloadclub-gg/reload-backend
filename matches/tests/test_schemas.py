from model_bakery import baker

from core.tests import TestCase
from matches.api import schemas
from matches.models import Match, MatchPlayer
from matchmaking.tests import mixins


class MatchesSchemasTestCase(mixins.TeamsMixin, TestCase):
    def test_match_schema(self):
        match = baker.make(Match)
        payload = schemas.MatchSchema.from_orm(match).dict()

        expected_payload = {
            'id': match.id,
            'create_date': match.create_date,
            'start_date': match.start_date,
            'end_date': match.end_date,
            'winner_team': match.winner_team,
            'status': match.status,
            'team_a_score': match.team_a_score,
            'team_b_score': match.team_b_score,
            'game_type': match.game_type,
            'game_mode': match.game_mode,
            'players': [],
            'rounds': match.rounds,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_player_schema(self):
        match = baker.make(Match)
        match_player = baker.make(MatchPlayer, match=match, user=self.user_1)

        payload = schemas.MatchPlayerSchema.from_orm(match_player).dict()
        expected_payload = {
            'id': match_player.id,
            'user': match_player.user.id,
            'team': match_player.team,
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
            'leg_shots': 0,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_with_players_schema(self):
        match = baker.make(Match)
        baker.make(MatchPlayer, match=match, user=self.user_1, team=Match.Teams.TEAM_A)
        baker.make(MatchPlayer, match=match, user=self.user_2, team=Match.Teams.TEAM_A)
        baker.make(MatchPlayer, match=match, user=self.user_3, team=Match.Teams.TEAM_A)
        baker.make(MatchPlayer, match=match, user=self.user_4, team=Match.Teams.TEAM_A)
        baker.make(MatchPlayer, match=match, user=self.user_5, team=Match.Teams.TEAM_A)
        baker.make(MatchPlayer, match=match, user=self.user_6, team=Match.Teams.TEAM_B)
        baker.make(MatchPlayer, match=match, user=self.user_7, team=Match.Teams.TEAM_B)
        baker.make(MatchPlayer, match=match, user=self.user_8, team=Match.Teams.TEAM_B)
        baker.make(MatchPlayer, match=match, user=self.user_9, team=Match.Teams.TEAM_B)
        baker.make(MatchPlayer, match=match, user=self.user_10, team=Match.Teams.TEAM_B)

        payload = schemas.MatchSchema.from_orm(match).dict()

        expected_payload = {
            'id': match.id,
            'create_date': match.create_date,
            'start_date': match.start_date,
            'end_date': match.end_date,
            'winner_team': match.winner_team,
            'status': match.status,
            'team_a_score': match.team_a_score,
            'team_b_score': match.team_b_score,
            'game_type': match.game_type,
            'game_mode': match.game_mode,
            'players': [
                schemas.MatchPlayerSchema.from_orm(match_player)
                for match_player in match.matchplayer_set.all()
            ],
            'rounds': match.rounds,
        }
        self.assertDictEqual(payload, expected_payload)
