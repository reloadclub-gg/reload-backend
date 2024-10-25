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
        self.user_1.add_session()
        self.user_2.add_session()
        self.user_3.add_session()
        self.user_4.add_session()
        self.user_5.add_session()
        self.user_6.add_session()
        self.user_7.add_session()
        self.user_8.add_session()
        self.user_9.add_session()
        self.user_10.add_session()

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
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
        self.assertEqual(
            team.players_count, self.lobby1.players_count + self.lobby2.players_count
        )

    def test_ready(self):
        self.lobby1.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        self.assertFalse(team1.ready)

        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()
        self.lobby5.start_queue()
        self.lobby6.start_queue()

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
        self.lobby1.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        self.assertFalse(team1.ready)

        self.lobby2.start_queue()
        self.lobby3.start_queue()
        team2 = Team.create(lobbies_ids=[self.lobby2.id, self.lobby3.id])
        self.assertTrue(team2.ready)

    def test_get_all(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()
        self.lobby5.start_queue()
        self.lobby6.start_queue()
        team1 = Team.create(lobbies_ids=[self.lobby1.id])
        team2 = Team.create(lobbies_ids=[self.lobby2.id])
        team3 = Team.create(
            lobbies_ids=[self.lobby3.id, self.lobby4.id, self.lobby5.id, self.lobby6.id]
        )

        teams = Team.get_all()
        self.assertCountEqual(teams, [team1, team2, team3])

    def test_remove_lobby(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()
        self.lobby5.start_queue()
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
        self.lobby1.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id])
        obj = Team.get_by_id(team.id)

        self.assertIsNotNone(obj)
        self.assertEqual(team.id, obj.id)

        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()
        self.lobby5.start_queue()
        self.lobby6.start_queue()
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
                ]
            )

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

    def test_overall(self):
        self.user_1.account.level = 5
        self.user_1.account.save()
        self.user_2.account.level = 4
        self.user_2.account.save()

        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team = Team.create([self.lobby1.id])
        self.assertEqual(team.overall, 5)

    def test_get_all_not_ready(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()

        team1 = Team.create([self.lobby1.id])

        self.lobby3.start_queue()
        self.lobby6.start_queue()

        team3 = Team.create([self.lobby3.id])

        not_ready = Team.get_all_not_ready()
        self.assertCountEqual([team1, team3], not_ready)

    def test_get_by_lobby_id(self):
        self.lobby1.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id])
        obj = Team.get_by_lobby_id(self.lobby1.id)
        self.assertEqual(team, obj)

        with self.assertRaises(TeamException):
            Team.get_by_lobby_id("unknown_lobby_id")

    def test_delete(self):
        self.lobby1.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id])
        team.delete()

        self.assertIsNone(Team.get_by_id(team.id))

        with self.assertRaises(TeamException):
            Team.get_by_id(team.id, raise_error=True)

    def test_mode(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id, self.lobby3.id])
        self.assertEqual(team.mode, Lobby.ModeChoices.COMP)

    # def test_min_max_overall_by_queue_time(self):
    #     self.lobby1.start_queue()
    #     now_minus_100 = (timezone.now() - datetime.timedelta(seconds=100)).isoformat()
    #     cache.set(f"{self.lobby1.cache_key}:queue", now_minus_100)

    #     self.user_2.account.level = 3
    #     self.user_2.account.save()
    #     self.lobby2.start_queue()

    #     team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
    #     self.assertEqual(team.min_max_overall_by_queue_time, (0, 6))

    def test_overall_match(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])
        match = Team.overall_match(team, self.lobby3)
        self.assertTrue(match)

        elapsed_time = (timezone.now() - datetime.timedelta(seconds=100)).isoformat()
        cache.set(f"{self.lobby1.cache_key}:queue", elapsed_time)
        cache.set(f"{self.lobby2.cache_key}:queue", elapsed_time)
        cache.set(f"{self.lobby3.cache_key}:queue", elapsed_time)

        self.user_4.account.level = 4
        self.user_4.account.save()
        self.lobby4.start_queue()

        match = Team.overall_match(team, self.lobby4)
        self.assertTrue(match)

    # def test_overall_not_match(self):
    #     self.lobby1.start_queue()
    #     self.lobby2.start_queue()
    #     team = Team.create(lobbies_ids=[self.lobby1.id, self.lobby2.id])

    #     self.user_3.account.level = 6
    #     self.user_3.account.save()
    #     self.lobby3.start_queue()

    #     match = Team.overall_match(team, self.lobby3)
    #     self.assertFalse(match)

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

    # def test_get_opponent_team_overall_queue_time(self):
    #     self.lobby1.set_public()
    #     Lobby.move(self.user_2.id, self.lobby1.id)
    #     Lobby.move(self.user_3.id, self.lobby1.id)
    #     Lobby.move(self.user_4.id, self.lobby1.id)
    #     Lobby.move(self.user_5.id, self.lobby1.id)
    #     self.lobby1.start_queue()
    #     team1 = Team.create(lobbies_ids=[self.lobby1.id])

    #     self.user_8.account.level = 5
    #     self.user_8.account.save()

    #     self.lobby6.set_public()
    #     Lobby.move(self.user_7.id, self.lobby6.id)
    #     Lobby.move(self.user_8.id, self.lobby6.id)
    #     Lobby.move(self.user_9.id, self.lobby6.id)
    #     Lobby.move(self.user_10.id, self.lobby6.id)
    #     self.lobby6.start_queue()
    #     team = Team.create(lobbies_ids=[self.lobby6.id])

    #     opponent = team.get_opponent_team()
    #     self.assertIsNone(opponent)

    #     elapsed_time = (timezone.now() - datetime.timedelta(seconds=140)).isoformat()
    #     cache.set(f'{self.lobby1.cache_key}:queue', elapsed_time)
    #     opponent = team.get_opponent_team()
    #     self.assertEqual(opponent, team1)

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

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    def test_add_lobby_full(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        team = Team.create(lobbies_ids=[self.lobby1.id])
        self.assertTrue(team.ready)
        with self.assertRaises(TeamException):
            team.add_lobby(self.lobby2.id)

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    def test_remove_lobby_pre_match(self):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        t1 = Team.create(lobbies_ids=[self.lobby1.id])
        t2 = Team.create(lobbies_ids=[self.lobby2.id])
        self.assertTrue(t1.ready)
        self.assertTrue(t2.ready)
        pm = PreMatch.create(t1.id, t2.id, t1.mode)

        self.assertIsNotNone(t1.pre_match_id)
        self.assertIsNotNone(t2.pre_match_id)

        with self.assertRaises(TeamException):
            t1.remove_lobby(self.lobby1.id)

        PreMatch.delete(pm.id)
        t1.remove_lobby(self.lobby1.id)
        t2.remove_lobby(self.lobby2.id)

        self.assertEqual(PreMatch.get_all(), [])
        self.assertEqual(Team.get_all(), [])


class PreMatchModelTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.add_session()
        self.user_2.add_session()
        self.user_3.add_session()
        self.user_4.add_session()
        self.user_5.add_session()
        self.user_6.add_session()
        self.user_7.add_session()
        self.user_8.add_session()
        self.user_9.add_session()
        self.user_10.add_session()
        self.user_11.add_session()
        self.user_12.add_session()
        self.user_13.add_session()
        self.user_14.add_session()
        self.user_15.add_session()

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

        self.lobby1.start_queue()
        self.lobby2.start_queue()
        self.lobby3.start_queue()
        self.lobby4.start_queue()
        self.lobby5.start_queue()

        self.team1 = Team.create(
            [
                self.lobby1.id,
                self.lobby2.id,
                self.lobby3.id,
                self.lobby4.id,
                self.lobby5.id,
            ]
        )
        self.lobby6.start_queue()
        self.lobby7.start_queue()
        self.lobby8.start_queue()
        self.lobby9.start_queue()
        self.lobby10.start_queue()
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
            PreMatch.create(
                self.team1.id,
                self.team2.id,
                self.team1.mode,
            )
        self.assertEqual(PreMatch.get_auto_id(), 10)

    def test_create(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        pre_match_model = PreMatch.get_by_id(pre_match.id)
        self.assertEqual(pre_match, pre_match_model)

    def test_set_player_ready(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        self.assertEqual(len(pre_match.players_ready), 0)
        pre_match.set_player_ready(self.user_1.id)
        self.assertEqual(len(pre_match.players_ready), 1)

    def test_ready(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )

        self.assertFalse(pre_match.ready)

        for player in pre_match.players:
            pre_match.set_player_ready(player.id)

        self.assertTrue(pre_match.ready)

    def test_countdown(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        self.assertEqual(pre_match.countdown, 30)
        time.sleep(2)
        self.assertEqual(pre_match.countdown, 28)

    def test_teams(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        self.assertEqual(pre_match.teams[0], self.team1)
        self.assertEqual(pre_match.teams[1], self.team2)

    def test_players(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        self.assertEqual(len(pre_match.players), 10)

    def test_get_by_team_id(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )

        result1 = PreMatch.get_by_team_id(self.team1.id)
        self.assertEqual(pre_match, result1)

        result2 = PreMatch.get_by_team_id(self.team2.id)
        self.assertEqual(pre_match, result2)

        result3 = PreMatch.get_by_team_id(self.team1.id, self.team2.id)
        self.assertEqual(pre_match, result3)

    def test_delete_all_keys(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        self.assertGreaterEqual(len(cache.keys(f"{pre_match.cache_key}*")), 1)

        PreMatch.delete(pre_match.id)
        self.assertGreaterEqual(len(cache.keys(f"{pre_match.cache_key}*")), 0)

    def test_get_all(self):
        all_pre_matches = PreMatch.get_all()
        self.assertEqual(len(all_pre_matches), 0)

        PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        all_pre_matches = PreMatch.get_all()
        self.assertEqual(len(all_pre_matches), 1)

    def test_get_by_player_id(self):
        PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        pre_match = PreMatch.get_by_player_id(player_id=self.user_1.id)
        self.assertIsNotNone(pre_match)

        pre_match = PreMatch.get_by_player_id(player_id=self.user_15.id)
        self.assertIsNone(pre_match)

    def test_delete(self):
        pm = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        PreMatch.delete(pm.id)
        with self.assertRaises(PreMatchException):
            PreMatch.get_by_id(pm.id)

        PreMatch.delete(pm.id)
        pm = PreMatch.get_by_id(pm.id, fail_silently=True)
        self.assertIsNone(pm)
