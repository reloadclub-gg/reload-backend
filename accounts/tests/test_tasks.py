from unittest import mock

from django.contrib.auth import get_user_model
from django.utils import timezone
from model_bakery import baker

from core.tests import TestCase
from lobbies.models import Lobby

from .. import tasks
from ..models import UserLogin
from . import mixins

User = get_user_model()


class AccountsTasksTestCase(mixins.UserWithFriendsMixin, TestCase):
    @mock.patch('accounts.tasks.ws_expire_player_invites')
    @mock.patch('accounts.tasks.handle_player_move')
    @mock.patch('accounts.tasks.ws_friend_update_or_create')
    @mock.patch('accounts.tasks.websocket.ws_user_logout')
    def test_watch_user_status_change_offline(
        self,
        mock_user_logout_ws,
        mock_friend_update,
        mock_lobby_move,
        mock_expire_invites,
    ):
        self.user.auth.add_session()

        self.friend1.auth.add_session()
        self.friend1.auth.expire_session(seconds=0)

        tasks.watch_user_status_change(self.friend1.id)
        mock_user_logout_ws.assert_called_once()
        mock_friend_update.assert_called_once()
        mock_expire_invites.assert_called_once()
        mock_lobby_move.assert_not_called()

    @mock.patch('accounts.tasks.ws_expire_player_invites')
    @mock.patch('accounts.tasks.handle_player_move')
    @mock.patch('accounts.tasks.ws_friend_update_or_create')
    @mock.patch('accounts.tasks.websocket.ws_user_logout')
    def test_watch_user_status_change_offline_with_lobby(
        self,
        mock_user_logout_ws,
        mock_friend_update,
        mock_lobby_move,
        mock_expire_invites,
    ):
        self.user.auth.add_session()

        self.friend1.auth.add_session()
        Lobby.create(owner_id=self.friend1.id)
        self.friend1.auth.expire_session(seconds=0)

        tasks.watch_user_status_change(self.friend1.id)
        mock_user_logout_ws.assert_called_once()
        mock_friend_update.assert_called_once()
        mock_expire_invites.assert_called_once()
        mock_lobby_move.assert_called_once()

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

    def test_watch_user_status_change(self):
        user = baker.make(User)
        tasks.watch_user_status_change(user.id)
