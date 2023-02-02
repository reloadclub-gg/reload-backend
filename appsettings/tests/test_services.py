from core.tests import TestCase

from ..models import AppSettings
from ..services import check_invite_required


class CheckInviteRequiredTestCase(TestCase):
    def test_check_invite_required_has_true(self):
        self.assertFalse(check_invite_required())
        AppSettings.set_bool('Invite Required', True)
        self.assertTrue(check_invite_required())
