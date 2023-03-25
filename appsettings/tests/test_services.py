from django.conf import settings

from core.tests import TestCase

from ..models import AppSettings
from ..services import (
    check_invite_required,
    matches_limit_per_server,
    matches_limit_per_server_gap,
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
