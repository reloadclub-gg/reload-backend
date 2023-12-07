from django.utils import timezone
from model_bakery import baker

from core.tests import TestCase
from core.utils import get_full_file_path
from matches.models import Match, MatchPlayer, Server
from pre_matches.tests.mixins import TeamsMixin
from profiles.api import schemas
from store.models import Item


class ProfilesSchemasTestCase(TeamsMixin, TestCase):
    def test_profile_schema(self):
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

        self.user_1.account.social_handles.update({'twitch': 'username'})
        self.user_1.account.save()

        active_header = self.user_1.useritem_set.filter(
            item__item_type=Item.ItemType.DECORATIVE,
            item__subtype=Item.SubType.PROFILE,
            in_use=True,
        ).first()

        payload = schemas.ProfileSchema.from_orm(self.user_1.account).dict()
        expected_payload = {
            'username': self.user_1.steam_user.username,
            'level': self.user_1.account.level,
            'level_points': self.user_1.account.level_points,
            'highest_level': self.user_1.account.highest_level,
            'social_handles': {
                'steam': self.user_1.account.steamid,
                'twitch': 'username',
            },
            'user_id': self.user_1.id,
            'avatar': self.user_1.account.avatar_dict,
            'matches_played': self.user_1.account.get_matches_played_count(),
            'matches_won': self.user_1.account.matches_won,
            'highest_win_streak': self.user_1.account.highest_win_streak,
            'latest_matches_results': self.user_1.account.get_latest_matches_results(),
            'most_kills_in_a_match': self.user_1.account.get_most_stat_in_match(
                'kills'
            ),
            'most_damage_in_a_match': self.user_1.account.get_most_stat_in_match(
                'damage'
            ),
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
                'rounds_played': 32,
                'clutches': 0,
                'shots_hit': 0,
                'adr': '9.38',
                'kdr': '12.50',
                'kda': '12.50',
                'ahk': '0.00',
                'ahr': '0.00',
                'hsk': 0,
                'accuracy': 0,
                'head_accuracy': 0,
                'chest_accuracy': 0,
                'others_accuracy': 0,
            },
            'date_joined': self.user_1.date_joined.isoformat(),
            'status': self.user_1.status,
            'header': get_full_file_path(active_header) if active_header else None,
        }

        self.assertDictEqual(payload, expected_payload)
