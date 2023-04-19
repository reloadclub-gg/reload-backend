from django.conf import settings

from core.tests import TestCase

from ..models import AppSettings
from ..services import (
    check_invite_required,
    matches_limit_per_server,
    matches_limit_per_server_gap,
    max_notification_history_count_per_player,
    player_max_level,
    player_max_level_points,
    player_max_losing_level_points,
)


class CheckInviteRequiredTestCase(TestCase):
    def test_check_invite_required(self):
        self.assertEqual(check_invite_required(), settings.APP_INVITE_REQUIRED)
        AppSettings.set_bool('Invite Required', True)
        self.assertTrue(check_invite_required())
        AppSettings.set_bool('Invite Required', False)
        self.assertFalse(check_invite_required())

    def test_matches_limit_per_server(self):
        self.assertEqual(matches_limit_per_server(), settings.MATCHES_LIMIT_PER_SERVER)
        AppSettings.set_int('Matches Limit', 5)
        self.assertEqual(matches_limit_per_server(), 5)

    def test_matches_limit_per_server_gap(self):
        self.assertEqual(
            matches_limit_per_server_gap(), settings.MATCHES_LIMIT_PER_SERVER_GAP
        )
        AppSettings.set_int('Matches Limit Gap', 1)
        self.assertEqual(matches_limit_per_server_gap(), 1)

    def test_player_max_level(self):
        self.assertEqual(player_max_level(), settings.PLAYER_MAX_LEVEL)
        AppSettings.set_int('Player Max Level', 1)
        self.assertEqual(player_max_level(), 1)

    def test_player_max_level_points(self):
        self.assertEqual(player_max_level_points(), settings.PLAYER_MAX_LEVEL_POINTS)
        AppSettings.set_int('Player Max Level Points', 1)
        self.assertEqual(player_max_level_points(), 1)

    def test_player_max_losing_level_points(self):
        self.assertEqual(
            player_max_losing_level_points(), settings.PLAYER_MAX_LOSE_LEVEL_POINTS
        )
        AppSettings.set_int('Player Max Losing Level Points', 1)
        self.assertEqual(player_max_losing_level_points(), 1)

    def test_max_notification_history_count_per_player(self):
        self.assertEqual(
            max_notification_history_count_per_player(),
            settings.MAX_NOTIFICATION_HISTORY_COUNT_PER_PLAYER,
        )
        AppSettings.set_int('Max Notification Count Per Player', 1)
        self.assertEqual(max_notification_history_count_per_player(), 1)
