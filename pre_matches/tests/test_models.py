import datetime
import time

from django.test import override_settings
from django.utils import timezone

from accounts.models import User
from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase, cache
from lobbies.models import Lobby

from ..models import PreMatch, PreMatchException, Team, TeamException


class TeamModelTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()
        self.user_7.auth.add_session()
        self.user_8.auth.add_session()
        self.user_9.auth.add_session()
        self.user_10.auth.add_session()

        self.lobby1 = Lobby.create(owner_id=self.user_1.id)
        self.lobby2 = Lobby.create(owner_id=self.user_2.id)
        self.lobby3 = Lobby.create(owner_id=self.user_3.id)
        self.lobby4 = Lobby.create(owner_id=self.user_4.id)
        self.lobby5 = Lobby.create(owner_id=self.user_5.id)
        self.lobby6 = Lobby.create(owner_id=self.user_6.id)
        self.lobby7 = Lobby.create(owner_id=self.user_7.id)
        self.lobby8 = Lobby.create(owner_id=self.user_8.id)
        self.lobby9 = Lobby.create(owner_id=self.user_9.id)
        self.lobby10 = Lobby.create(owner_id=self.user_10.id)

    def test_players_count(self):
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
        self.assertEqual(
            team.players_count, self.lobby1.players_count + self.lobby2.players_count
        )

    def test_build(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()
        self.lobby5.start_queue()
        self.lobby6.start_queue()

        team = Team.build(self.lobby1)
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)
        self.assertEqual(team.players_count, self.lobby1.max_players)

    def test_build_skips(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)

        self.lobby4.set_public()
        Lobby.move(self.user_5.id, self.lobby4.id)

        self.lobby1.start_queue()
        self.lobby4.set_mode(1)
        self.lobby4.start_queue()
        self.lobby6.start_queue()

        team = Team.build(self.lobby1)
        self.assertEqual(team.lobbies_ids, [self.lobby1.id, self.lobby6.id])
        self.assertEqual(team.players_count, 4)
        team.delete()

        self.user_6.account.level = 7
        self.user_6.account.save()

        team = Team.build(self.lobby1)
        self.assertIsNone(team)

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    def test_build_with_other_teams(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        team = Team.build(self.lobby1)
        self.assertTrue(team.ready)

        self.lobby3.start_queue()
        team2 = Team.build(self.lobby3)
        self.assertIsNone(team2)

        self.lobby4.start_queue()
        team2 = Team.build(self.lobby3)
        self.assertIsNotNone(team2)
        self.assertTrue(team2.ready)

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    def test_build_with_other_teams_oversized(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        self.assertEqual(self.lobby1.players_count, 2)

        self.lobby1.start_queue()
        team = Team.build(self.lobby1)
        self.assertTrue(team.ready)

        self.lobby3.start_queue()
        team2 = Team.build(self.lobby3)
        self.assertIsNotNone(team2)
        self.assertTrue(team2.ready)

    def test_ready(self):
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        self.assertFalse(team1.ready)

        team2 = Team.create(
            lobbies_ids=[
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
                self.lobby6.id,
            ]
        )

        self.assertTrue(team2.ready)

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    def test_ready_min_override(self):
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        self.assertFalse(team1.ready)

        team2 = Team.create(lobbies_ids=[self.lobby2.id, self.lobby3.id])
        self.assertTrue(team2.ready)

    def test_build_errors(self):
        Team.create(lobbies_ids=[self.lobby1.id])
        Team.create(lobbies_ids=[self.lobby2.id, self.lobby4.id])

        with self.assertRaises(TeamException):
            Team.build(self.lobby1)

        with self.assertRaises(TeamException):
            Team.build(self.lobby2)

        with self.assertRaises(TeamException):
            Team.build(self.lobby3)

        with self.assertRaises(TeamException):
            Team.build(self.lobby4)

        self.lobby5.start_queue()
        Team.build(self.lobby5)

    def test_get_all(self):
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        team2 = Team.create(lobbies_ids=[self.lobby2.id])
        team3 = Team.create(
            lobbies_ids=[self.lobby3.id, self.lobby4.id, self.lobby5.id, self.lobby6.id]
        )

        teams = Team.get_all()
        self.assertCountEqual(teams, [team1, team2, team3])

    def test_remove_lobby(self):
        team = Team.create(
            lobbies_ids=[
                self.lobby1.id,
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
            ]
        )
        team.remove_lobby(self.lobby3.id)
        self.assertFalse(team.ready)
        self.assertTrue(self.lobby3.id not in team.lobbies_ids)

        team.remove_lobby(self.lobby2.id)
        team.remove_lobby(self.lobby4.id)
        team.remove_lobby(self.lobby5.id)

        with self.assertRaises(TeamException):
            Team.get_by_id(team.id, raise_error=True)

    def test_create_and_get_by_id(self):
        team = Team.create(lobbies_ids=[self.lobby1.id])
        obj = Team.get_by_id(team.id)

        self.assertIsNotNone(obj)
        self.assertEqual(team.id, obj.id)

        team = Team.create(
            lobbies_ids=[
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
                self.lobby6.id,
            ]
        )
        obj = Team.get_by_id(team.id)

        self.assertIsNotNone(obj)
        self.assertEqual(team.id, obj.id)
        self.assertTrue(team.ready)

    def test_create_and_get_by_id_error(self):
        with self.assertRaises(TeamException):
            Team.create(
                lobbies_ids=[
                    self.lobby1.id,
                    self.lobby2.id,
                    self.lobby3.id,
                    self.lobby4.id,
                    self.lobby5.id,
                    self.lobby6.id,
                ]
            )

    def test_find(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team = Team.build(self.lobby1)
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)
        self.assertEqual(team.players_count, 2)
        self.assertEqual(len(team.lobbies_ids), 2)

        self.lobby3.start_queue()
        team2 = Team.find(self.lobby3)
        self.assertIsNotNone(team2)
        self.assertEqual(team.id, team2.id)

    def test_find_not_matching_overalls(self):
        self.user_3.account.level = 20
        self.user_3.account.save()

        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team = Team.build(self.lobby1)
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)
        self.assertEqual(team.players_count, 2)
        self.assertEqual(len(team.lobbies_ids), 2)

        self.lobby3.start_queue()
        team2 = Team.find(self.lobby3)
        self.assertIsNone(team2)

    def test_find_not_matching_mode(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        team = Team.build(self.lobby1)
        team_model = Team.get_by_id(team.id)
        self.assertEqual(team.id, team_model.id)

        self.lobby3.set_mode(1)
        self.lobby3.start_queue()
        team = Team.find(self.lobby3)
        self.assertIsNone(team)

    def test_overall(self):
        self.user_1.account.level = 5
        self.user_1.account.save()
        self.user_2.account.level = 4
        self.user_2.account.save()

        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team = Team.build(self.lobby1)
        self.assertEqual(team.overall, 5)

    def test_get_all_not_ready(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team1 = Team.build(self.lobby1)

        self.lobby3.start_queue()
        self.lobby6.start_queue()

        team3 = Team.build(self.lobby3)

        not_ready = Team.get_all_not_ready()
        self.assertCountEqual([team1, team3], not_ready)

    def test_get_by_lobby_id(self):
        team = Team.create(lobbies_ids=[self.lobby1.id])
        obj = Team.get_by_lobby_id(self.lobby1.id)
        self.assertEqual(team, obj)

        with self.assertRaises(TeamException):
            Team.get_by_lobby_id('unknown_lobby_id')

    def test_delete(self):
        team = Team.create(lobbies_ids=[self.lobby1.id])
        team.delete()

        self.assertIsNone(Team.get_by_id(team.id))

        with self.assertRaises(TeamException):
            Team.get_by_id(team.id, raise_error=True)

    def test_type_mode(self):
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id, self.lobby3.id])
        self.assertEqual(team.type_mode, ('competitive', 5))

    def test_min_max_overall_by_queue_time(self):
        self.lobby1.start_queue()
        now_minus_100 = (timezone.now() - datetime.timedelta(seconds=100)).isoformat()
        cache.set(f'{self.lobby1.cache_key}:queue', now_minus_100)

        self.user_2.account.level = 3
        self.user_2.account.save()
        self.lobby2.start_queue()

        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
        self.assertEqual(team.min_max_overall_by_queue_time, (0, 4))

    def test_overall_match(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
        match = Team.overall_match(team, self.lobby3)
        self.assertTrue(match)

        elapsed_time = (timezone.now() - datetime.timedelta(seconds=100)).isoformat()
        cache.set(f'{self.lobby1.cache_key}:queue', elapsed_time)
        cache.set(f'{self.lobby2.cache_key}:queue', elapsed_time)
        cache.set(f'{self.lobby3.cache_key}:queue', elapsed_time)

        self.user_4.account.level = 4
        self.user_4.account.save()
        self.lobby4.start_queue()

        match = Team.overall_match(team, self.lobby4)
        self.assertTrue(match)

    def test_overall_not_match(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])

        self.user_3.account.level = 6
        self.user_3.account.save()
        self.lobby3.start_queue()

        match = Team.overall_match(team, self.lobby3)
        self.assertFalse(match)

    def test_get_opponent_team(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)
        Lobby.move(self.user_4.id, self.lobby1.id)
        Lobby.move(self.user_5.id, self.lobby1.id)
        self.lobby1.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])

        self.lobby6.set_public()
        Lobby.move(self.user_7.id, self.lobby6.id)
        Lobby.move(self.user_8.id, self.lobby6.id)
        Lobby.move(self.user_9.id, self.lobby6.id)
        Lobby.move(self.user_10.id, self.lobby6.id)
        self.lobby6.start_queue()
        team2 = Team.create(lobbies_ids=[self.lobby6.id])

        opponent = team2.get_opponent_team()
        self.assertEqual(opponent, team1)

    def test_get_opponent_team_overall_queue_time(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)
        Lobby.move(self.user_4.id, self.lobby1.id)
        Lobby.move(self.user_5.id, self.lobby1.id)
        self.lobby1.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])

        self.user_8.account.level = 5
        self.user_8.account.save()

        self.lobby6.set_public()
        Lobby.move(self.user_7.id, self.lobby6.id)
        Lobby.move(self.user_8.id, self.lobby6.id)
        Lobby.move(self.user_9.id, self.lobby6.id)
        Lobby.move(self.user_10.id, self.lobby6.id)
        self.lobby6.start_queue()
        team = Team.create(lobbies_ids=[self.lobby6.id])

        opponent = team.get_opponent_team()
        self.assertIsNone(opponent)

        elapsed_time = (timezone.now() - datetime.timedelta(seconds=140)).isoformat()
        cache.set(f'{self.lobby1.cache_key}:queue', elapsed_time)
        opponent = team.get_opponent_team()
        self.assertEqual(opponent, team1)

    def test_name(self):
        self.lobby1.set_public()
        Lobby.move(self.user_2.id, self.lobby1.id)
        Lobby.move(self.user_3.id, self.lobby1.id)
        Lobby.move(self.user_4.id, self.lobby1.id)
        Lobby.move(self.user_5.id, self.lobby1.id)
        self.lobby1.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        players_ids = [lobby.players_ids for lobby in team1.lobbies][0]
        players_usernames = [
            User.objects.get(pk=player_id).steam_user.username
            for player_id in players_ids
        ]
        self.assertIsNotNone(team1.name)
        self.assertTrue(team1.name in players_usernames)


class PreMatchModelTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()
        self.user_7.auth.add_session()
        self.user_8.auth.add_session()
        self.user_9.auth.add_session()
        self.user_10.auth.add_session()
        self.user_11.auth.add_session()
        self.user_12.auth.add_session()
        self.user_13.auth.add_session()
        self.user_14.auth.add_session()
        self.user_15.auth.add_session()

        self.lobby1 = Lobby.create(owner_id=self.user_1.id)
        self.lobby2 = Lobby.create(owner_id=self.user_2.id)
        self.lobby3 = Lobby.create(owner_id=self.user_3.id)
        self.lobby4 = Lobby.create(owner_id=self.user_4.id)
        self.lobby5 = Lobby.create(owner_id=self.user_5.id)
        self.lobby6 = Lobby.create(owner_id=self.user_6.id)
        self.lobby7 = Lobby.create(owner_id=self.user_7.id)
        self.lobby8 = Lobby.create(owner_id=self.user_8.id)
        self.lobby9 = Lobby.create(owner_id=self.user_9.id)
        self.lobby10 = Lobby.create(owner_id=self.user_10.id)
        self.lobby11 = Lobby.create(owner_id=self.user_11.id)
        self.lobby12 = Lobby.create(owner_id=self.user_12.id)
        self.lobby13 = Lobby.create(owner_id=self.user_13.id)
        self.lobby14 = Lobby.create(owner_id=self.user_14.id)
        self.lobby15 = Lobby.create(owner_id=self.user_15.id)

        self.team1 = Team.create(
            [
                self.lobby1.id,
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
            ]
        )
        self.team2 = Team.create(
            [
                self.lobby6.id,
                self.lobby7.id,
                self.lobby8.id,
                self.lobby9.id,
                self.lobby10.id,
            ]
        )

    def test_auto_id(self):
        for _ in range(0, 10):
            PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(PreMatch.get_auto_id(), 10)

    def test_create(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        pre_match_model = PreMatch.get_by_id(pre_match.id)
        self.assertEqual(pre_match, pre_match_model)

    def test_start_players_ready_countdown(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        ready_time = cache.get(f'{pre_match.cache_key}:ready_time')
        self.assertIsNone(ready_time)

        pre_match.start_players_ready_countdown()
        ready_time = cache.get(f'{pre_match.cache_key}:ready_time')
        self.assertIsNotNone(ready_time)

    def test_set_player_ready(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)
        pre_match.start_players_ready_countdown()
        self.assertEqual(len(pre_match.players_ready), 0)

        pre_match.set_player_ready(self.user_1.id)
        self.assertEqual(len(pre_match.players_ready), 1)

    def test_set_player_ready_wrong_state(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        with self.assertRaises(PreMatchException):
            pre_match.set_player_ready(self.user_1.id)

    def test_set_player_lock_in(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(len(pre_match.players_in), 0)

        pre_match.set_player_lock_in(self.user_1.id)
        self.assertEqual(len(pre_match.players_in), 1)

    def test_set_player_lock_in_wrong_state(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        with self.assertRaises(PreMatchException):
            pre_match.set_player_lock_in(self.user_1.id)

    def test_state(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(pre_match.state, PreMatch.Config.STATES.get('pre_start'))

        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)
        self.assertEqual(pre_match.state, PreMatch.Config.STATES.get('idle'))

        pre_match.start_players_ready_countdown()
        self.assertEqual(pre_match.state, PreMatch.Config.STATES.get('lock_in'))

        for player in pre_match.players:
            pre_match.set_player_ready(player.id)

        self.assertEqual(pre_match.state, PreMatch.Config.STATES.get('ready'))

    def test_state_cancelled(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        seconds_with_gap = (
            PreMatch.Config.READY_COUNTDOWN - PreMatch.Config.READY_COUNTDOWN_GAP
        )
        elapsed_time = timezone.timedelta(seconds=seconds_with_gap)
        past_time = (timezone.now() - elapsed_time).isoformat()
        cache.set(f'{pre_match.cache_key}:ready_time', past_time)

        self.assertEqual(pre_match.state, PreMatch.Config.STATES.get('cancelled'))

    def test_countdown(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        pre_match.start_players_ready_countdown()
        self.assertEqual(pre_match.countdown, 30)
        time.sleep(2)
        self.assertEqual(pre_match.countdown, 28)

    def test_teams(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(pre_match.teams[0], self.team1)
        self.assertEqual(pre_match.teams[1], self.team2)

    def test_players(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(len(pre_match.players), 10)

    def test_get_by_team_id(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)

        result1 = PreMatch.get_by_team_id(self.team1.id)
        self.assertEqual(pre_match, result1)

        result2 = PreMatch.get_by_team_id(self.team2.id)
        self.assertEqual(pre_match, result2)

        result3 = PreMatch.get_by_team_id(self.team1.id, self.team2.id)
        self.assertEqual(pre_match, result3)

    def test_delete_all_keys(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertGreaterEqual(len(cache.keys(f'{pre_match.cache_key}*')), 1)

        PreMatch.delete(pre_match.id)
        self.assertGreaterEqual(len(cache.keys(f'{pre_match.cache_key}*')), 0)

    def test_get_all(self):
        all_pre_matches = PreMatch.get_all()
        self.assertEqual(len(all_pre_matches), 0)

        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        pre_match.start_players_ready_countdown()
        all_pre_matches = PreMatch.get_all()
        self.assertEqual(len(all_pre_matches), 1)

    def test_get_by_player_id(self):
        PreMatch.create(self.team1.id, self.team2.id)
        pre_match = PreMatch.get_by_player_id(player_id=self.user_1.id)
        self.assertIsNotNone(pre_match)

        pre_match = PreMatch.get_by_player_id(player_id=self.user_15.id)
        self.assertIsNone(pre_match)
