from ..services import check_invite_required
from ..models import AppSettings
from core.tests import TestCase


class CheckInviteRequiredTestCase(TestCase):
    def test_check_invite_required_has_true(self):
        self.assertTrue(check_invite_required())

    def test_check_invite_required_has_false(self):
        AppSettings.objects.filter(name='Invite Required').update(value='0')

        self.assertFalse(check_invite_required())
