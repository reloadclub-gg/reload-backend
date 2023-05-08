from django.utils import timezone
from model_bakery import baker

from accounts.api import schemas
from core.tests import TestCase
from matches.api.schemas import MatchSchema
from matches.models import Match, MatchPlayer, Server
from matchmaking.api.schemas import LobbySchema
from matchmaking.models import Lobby
from matchmaking.tests.mixins import TeamsMixin
from notifications.api.schemas import NotificationSchema
from steam import Steam

from . import mixins


class AccountsSchemasTestCase(mixins.UserWithFriendsMixin, TestCase):
    def test_account_friend_schema(self):
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        payload = schemas.FriendAccountSchema.from_orm(self.user.account).dict()

        expected_payload = {
            'steamid': self.user.account.steamid,
            'level': self.user.account.level,
            'level_points': self.user.account.level_points,
            'id': self.user.id,
            'username': self.user.steam_user.username,
            'avatar': {
                'small': Steam.build_avatar_url(self.user.steam_user.avatarhash),
                'medium': Steam.build_avatar_url(
                    self.user.steam_user.avatarhash, 'medium'
                ),
                'large': Steam.build_avatar_url(
                    self.user.steam_user.avatarhash, 'full'
                ),
            },
            'is_online': self.user.is_online,
            'status': self.user.status,
            'lobby': LobbySchema.from_orm(self.user.account.lobby).dict(),
            'steam_url': self.user.steam_user.profileurl,
            'match': MatchSchema.from_orm(self.user.account.match)
            if self.user.account.match
            else None,
        }

        self.assertDictEqual(payload, expected_payload)

    def test_account_schema(self):
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        payload = schemas.AccountSchema.from_orm(self.user.account).dict()

        expected_payload = {
            'steamid': self.user.account.steamid,
            'level': self.user.account.level,
            'level_points': self.user.account.level_points,
            'is_verified': self.user.account.is_verified,
            'username': self.user.steam_user.username,
            'avatar': {
                'small': Steam.build_avatar_url(self.user.steam_user.avatarhash),
                'medium': Steam.build_avatar_url(
                    self.user.steam_user.avatarhash, 'medium'
                ),
                'large': Steam.build_avatar_url(
                    self.user.steam_user.avatarhash, 'full'
                ),
            },
            'lobby': LobbySchema.from_orm(self.user.account.lobby).dict(),
            'friends': [
                schemas.FriendAccountSchema.from_orm(x).dict()
                for x in self.user.account.friends
            ],
            'lobby_invites': [
                schemas.LobbyInviteSchema.from_orm(x).dict()
                for x in self.user.account.lobby_invites
            ],
            'lobby_invites_sent': [
                schemas.LobbyInviteSchema.from_orm(x).dict()
                for x in self.user.account.lobby_invites_sent
            ],
            'pre_match': self.user.account.pre_match,
            'steam_url': self.user.steam_user.profileurl,
            'match': MatchSchema.from_orm(self.user.account.match)
            if self.user.account.match
            else None,
            'notifications': [
                NotificationSchema.from_orm(x).dict()
                for x in self.user.account.notifications
            ],
        }

        self.assertDictEqual(payload, expected_payload)

    def test_user_schema(self):
        self.user.auth.add_session()
        Lobby.create(self.user.id)
        payload = schemas.UserSchema.from_orm(self.user).dict()

        expected_payload = {
            'id': self.user.id,
            'email': self.user.email,
            'is_active': self.user.is_active,
            'account': schemas.AccountSchema.from_orm(self.user.account).dict(),
            'is_online': self.user.is_online,
            'status': self.user.status,
        }

        self.assertDictEqual(payload, expected_payload)


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
            'id': self.user_1.id,
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
            'status': self.user_1.status,
            'matches_played': len(self.user_1.account.matches_played),
            'match_wins': self.user_1.account.match_wins,
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
