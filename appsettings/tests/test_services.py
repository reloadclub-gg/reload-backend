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
        AppSettings.objects.create(name='Invite Required', value='0', kind='boolean')
        self.assertFalse(check_invite_required())

    def test_matches_limit_per_server(self):
        self.assertEqual(matches_limit_per_server(), settings.MATCHES_LIMIT_PER_SERVER)
        AppSettings.objects.create(name='Matches Limit', value='5', kind='integer')
        self.assertEqual(matches_limit_per_server(), 5)

    def test_matches_limit_per_server_gap(self):
        self.assertEqual(
            matches_limit_per_server_gap(),
            settings.MATCHES_LIMIT_PER_SERVER_GAP,
        )
        AppSettings.objects.create(name='Matches Limit Gap', value='1', kind='integer')
        self.assertEqual(matches_limit_per_server_gap(), 1)

    def test_player_max_level(self):
        self.assertEqual(player_max_level(), settings.PLAYER_MAX_LEVEL)
        AppSettings.objects.create(name='Player Max Level', value='1', kind='integer')
        self.assertEqual(player_max_level(), 1)

    def test_player_max_level_points(self):
        self.assertEqual(player_max_level_points(), settings.PLAYER_MAX_LEVEL_POINTS)
        AppSettings.objects.create(
            name='Player Max Level Points',
            value='1',
            kind='integer',
        )
        self.assertEqual(player_max_level_points(), 1)

    def test_player_max_losing_level_points(self):
        self.assertEqual(
            player_max_losing_level_points(),
            settings.PLAYER_MAX_LOSE_LEVEL_POINTS,
        )
        AppSettings.objects.create(
            name='Player Max Losing Level Points',
            value='1',
            kind='integer',
        )
        self.assertEqual(player_max_losing_level_points(), 1)

    def test_max_notification_history_count_per_player(self):
        self.assertEqual(
            max_notification_history_count_per_player(),
            settings.MAX_NOTIFICATION_HISTORY_COUNT_PER_PLAYER,
        )
        AppSettings.objects.create(
            name='Max Notification Count Per Player',
            value='1',
            kind='integer',
        )
        self.assertEqual(max_notification_history_count_per_player(), 1)
