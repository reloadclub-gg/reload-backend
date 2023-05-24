from unittest import mock

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.tests import TestCase
from matchmaking.models import Lobby

from .. import tasks
from ..models import UserLogin
from . import mixins

User = get_user_model()


class AccountsTasksTestCase(mixins.UserWithFriendsMixin, TestCase):
    @mock.patch('accounts.tasks.user_status_change')
    def test_watch_user_status_change_offline(self, mock_user_status_change):
        self.user.auth.add_session()

        self.friend1.auth.add_session()
        self.friend1.auth.expire_session(seconds=0)

        tasks.watch_user_status_change(self.friend1.id)
        mock_user_status_change.assert_called_once()

    @mock.patch('matchmaking.models.Lobby.move')
    def test_watch_user_status_change_to_offline_does_cancel_lobby(self, mock_quit):
        mock_quit.return_value = None
        self.user.auth.add_session()
        Lobby.create(owner_id=self.user.id)
        self.user.auth.expire_session(seconds=0)
        tasks.watch_user_status_change(self.user.id)
        mock_quit.assert_called_once()

    def test_decr_level_from_inactivity(self):
        self.user.account.level = 35
        self.user.account.level_points = 20
        self.user.account.save()

        self.assertEqual(self.user.account.level, 35)
        self.assertEqual(self.user.account.level_points, 20)

        self.user.userlogin_set.create(ip_address='1.1.1.1')
        tasks.decr_level_from_inactivity()
        self.user.account.refresh_from_db()
        self.assertEqual(self.user.account.level, 35)
        self.assertEqual(self.user.account.level_points, 20)

        l2 = self.user.userlogin_set.create(ip_address='2.2.2.2')
        l2.timestamp = timezone.now() - timezone.timedelta(days=91)
        l2.save()
        tasks.decr_level_from_inactivity()
        self.user.account.refresh_from_db()
        self.assertEqual(self.user.account.level, 35)
        self.assertEqual(self.user.account.level_points, 20)

        UserLogin.objects.all().delete()

        l3 = self.user.userlogin_set.create(ip_address='2.2.2.2')
        l3.timestamp = timezone.now() - timezone.timedelta(days=91)
        l3.save()
        tasks.decr_level_from_inactivity()
        self.user.account.refresh_from_db()
        self.assertEqual(self.user.account.level, 34)
        self.assertEqual(self.user.account.level_points, 0)

        # self.user.userlogin_set.create(
        #     ip_address='2.2.2.2',
        # )
        # tasks.decr_level_from_inactivity()
        # self.user.account.refresh_from_db()
        # self.assertEqual(self.user.account.level, 34)
        # self.assertEqual(self.user.account.level_points, 0)
