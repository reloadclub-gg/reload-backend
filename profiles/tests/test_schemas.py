from django.utils import timezone
from model_bakery import baker

from core.tests import TestCase
from matches.models import Match, MatchPlayer, Server
from matchmaking.tests.mixins import TeamsMixin
from profiles.api import schemas
from steam import Steam


class AccountsMatchesSchemasTestCase(TeamsMixin, TestCase):
    def test_profile(self):
        server = baker.make(Server)
        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10)
        match.matchteam_set.create(name=self.team2.name, score=6)
        match_player = baker.make(MatchPlayer, team=team1, user=self.user_1)
        kills_1 = match_player.stats.kills = 10
        dmg_1 = match_player.stats.damage = 100
        match_player.stats.save()

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10)
        match.matchteam_set.create(name=self.team2.name, score=6)
        match_player = baker.make(MatchPlayer, team=team1, user=self.user_1)
        kills_2 = match_player.stats.kills = 15
        dmg_2 = match_player.stats.damage = 200
        match_player.stats.save()

        payload = schemas.ProfileSchema.from_orm(self.user_1.account).dict()
        expected_payload = {
            'level': self.user_1.account.level,
            'level_points': self.user_1.account.level_points,
            'highest_level': self.user_1.account.highest_level,
            'user_id': self.user_1.id,
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
            'matches_played': len(self.user_1.account.matches_played),
            'matches_won': self.user_1.account.matches_won,
            'highest_win_streak': self.user_1.account.highest_win_streak,
            'latest_matches_results': self.user_1.account.get_latest_matches_results(),
            'stats': {
                'kills': kills_1 + kills_2,
                'deaths': 0,
                'assists': 0,
                'damage': dmg_1 + dmg_2,
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
                'most_kills_in_a_match': self.user_1.account.get_most_stat_in_match(
                    'kills'
                ),
                'most_damage_in_a_match': self.user_1.account.get_most_stat_in_match(
                    'damage'
                ),
            },
        }

        self.assertDictEqual(payload, expected_payload)
