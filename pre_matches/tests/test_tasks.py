from unittest import mock

from django.conf import settings
from django.test import override_settings
from django.utils import timezone

from core.redis import redis_client_instance as cache
from core.tests import TestCase
from lobbies.models import Lobby, PlayerDodges, PlayerRestriction

from .. import models, tasks
from . import mixins


class PreMatchTasksTestCase(mixins.TeamsMixin, TestCase):
    @mock.patch('pre_matches.tasks.ws_update_user')
    @mock.patch('pre_matches.tasks.ws_create_toast')
    @mock.patch('pre_matches.tasks.ws_friend_update_or_create')
    @mock.patch('pre_matches.tasks.websocket.ws_pre_match_delete')
    def test_cancel_match_after_countdown(
        self,
        mock_pre_match_delete,
        mock_friend_update,
        mock_create_toast,
        mock_update_user,
    ):
        pre_match = models.PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.type_mode[0],
            self.team1.type_mode[1],
        )

        for player in pre_match.players:
            pre_match.set_player_lock_in(player.id)

        player_ready = pre_match.players[0]
        player_dodged = pre_match.players[1]
        pre_match.set_player_ready(player_ready.id)
        past_time = (timezone.now() - timezone.timedelta(seconds=40)).isoformat()
        cache.set(f'{pre_match.cache_key}:ready_time', past_time)
        tasks.cancel_match_after_countdown(pre_match.id)
        dodge = PlayerDodges.objects.get(user_id=player_dodged.id)
        self.assertEqual(dodge.count, 1)

        mock_calls = [
            mock.call(self.user_1),
            mock.call(self.user_2),
        ]
        mock_pre_match_delete.assert_called_once()
        self.assertEqual(mock_create_toast.call_count, 9)
        mock_friend_update.assert_has_calls(mock_calls)
        mock_update_user.assert_has_calls(mock_calls)

        with self.assertRaises(models.PreMatchException):
            models.PreMatch.get_by_id(pre_match.id)

        with self.assertRaises(models.TeamException):
            models.Team.get_by_id(self.team1.id, raise_error=True)
            models.Team.get_by_id(self.team2.id, raise_error=True)

    @mock.patch('pre_matches.tasks.websocket.ws_pre_match_delete')
    def test_cancel_match_after_countdown_multiple_teams(
        self,
        mock_pre_match_delete,
    ):
        pre_match_1 = models.PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.type_mode[0],
            self.team1.type_mode[1],
        )
        for player in pre_match_1.players:
            pre_match_1.set_player_lock_in(player.id)

        pre_match_2 = models.PreMatch.create(
            self.team3.id,
            self.team4.id,
            self.team3.type_mode[0],
            self.team3.type_mode[1],
        )
        for player in pre_match_2.players:
            pre_match_2.set_player_lock_in(player.id)

        past_time = (timezone.now() - timezone.timedelta(seconds=15)).isoformat()
        cache.set(f'{pre_match_1.cache_key}:ready_time', past_time)

        past_time = (timezone.now() - timezone.timedelta(seconds=40)).isoformat()
        cache.set(f'{pre_match_1.cache_key}:ready_time', past_time)
        tasks.cancel_match_after_countdown(pre_match_1.id)

        past_time = (timezone.now() - timezone.timedelta(seconds=40)).isoformat()
        cache.set(f'{pre_match_2.cache_key}:ready_time', past_time)
        tasks.cancel_match_after_countdown(pre_match_2.id)

        self.assertEqual(mock_pre_match_delete.call_count, 2)

    @override_settings(
        PLAYER_DODGES_MIN_TO_RESTRICT=3,
        PLAYER_DODGES_MULTIPLIER=[1, 2, 5, 10, 20, 40, 60, 90],
    )
    def test_handle_dodges(self):
        self.assertEqual(PlayerDodges.objects.all().count(), 0)
        tasks.handle_dodges(self.user_1.account.lobby, [])
        self.assertEqual(PlayerDodges.objects.all().count(), 1)
        player_dodges = PlayerDodges.objects.get(user=self.user_1)
        self.assertEqual(player_dodges.count, 1)

        tasks.handle_dodges(self.user_1.account.lobby, [])
        self.assertEqual(PlayerDodges.objects.all().count(), 1)
        player_dodges = PlayerDodges.objects.get(user=self.user_1)
        self.assertEqual(player_dodges.count, 2)

        self.user_1.account.lobby.set_public()
        Lobby.move(self.user_2.id, self.user_1.account.lobby.id)
        self.assertEqual(PlayerRestriction.objects.all().count(), 0)
        tasks.handle_dodges(self.user_1.account.lobby, [self.user_2.id])
        self.assertEqual(PlayerDodges.objects.all().count(), 1)
        player_dodges = PlayerDodges.objects.get(user=self.user_1)
        self.assertEqual(player_dodges.count, 3)

        self.assertEqual(PlayerRestriction.objects.all().count(), 1)

        dodges_to_restrict = settings.PLAYER_DODGES_MIN_TO_RESTRICT
        dodges_multipliers = settings.PLAYER_DODGES_MULTIPLIER
        factor_idx = player_dodges.count - dodges_to_restrict
        if factor_idx > len(dodges_multipliers):
            factor_idx = len(dodges_multipliers) - 1
        factor = dodges_multipliers[factor_idx]
        lock_minutes = player_dodges.count * factor
        player_restriction = PlayerRestriction.objects.get(user=self.user_1)
        self.assertEqual(
            player_restriction.end_date.minute,
            (
                player_restriction.start_date + timezone.timedelta(minutes=lock_minutes)
            ).minute,
        )

        tasks.handle_dodges(self.user_1.account.lobby, [self.user_1.id])
        self.assertEqual(PlayerDodges.objects.all().count(), 2)
        player_dodges = PlayerDodges.objects.get(user=self.user_1)
        self.assertEqual(player_dodges.count, 3)
        player_dodges = PlayerDodges.objects.get(user=self.user_2)
        self.assertEqual(player_dodges.count, 1)
