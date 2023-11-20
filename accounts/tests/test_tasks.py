import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from model_bakery import baker

from core.tests import TestCase
from lobbies.models import Lobby
from lobbies.tasks import queue
from pre_matches.models import Team

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
        self.user.add_session()
        self.user.status = User.Status.ONLINE
        self.user.save()

        self.friend1.add_session()
        self.friend1.status = User.Status.ONLINE
        self.friend1.save()

        self.friend1.auth.expire_session(0)
        tasks.watch_user_status_change(self.friend1.id)
        mock_user_logout_ws.assert_called_once()
        mock_friend_update.assert_called_once()
        mock_expire_invites.assert_called_once()
        mock_lobby_move.assert_called_once()

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
        self.user.add_session()

        self.friend1.add_session()
        Lobby.create(owner_id=self.friend1.id)
        self.friend1.logout()

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

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('pre_matches.models.Team.remove_lobby')
    @mock.patch('accounts.tasks.cancel_pre_match')
    @mock.patch('accounts.tasks.ws_expire_player_invites')
    @mock.patch('accounts.tasks.handle_player_move')
    @mock.patch('accounts.tasks.ws_friend_update_or_create')
    @mock.patch('accounts.tasks.websocket.ws_user_logout')
    def test_watch_user_status_change_offline_with_pre_match(
        self,
        mock_user_logout_ws,
        mock_friend_update,
        mock_lobby_move,
        mock_expire_invites,
        mock_cancel_pre_match,
        mock_remove_lobby,
    ):
        self.user.add_session()
        self.friend1.add_session()
        l1 = Lobby.create(owner_id=self.friend1.id)
        l2 = Lobby.create(owner_id=self.user.id)
        l1.start_queue()
        l2.start_queue()
        queue()

        self.friend1.logout()
        tasks.watch_user_status_change(self.friend1.id)

        mock_user_logout_ws.assert_called_once()
        mock_friend_update.assert_called_once()
        mock_expire_invites.assert_called_once()
        mock_lobby_move.assert_called_once()
        mock_cancel_pre_match.assert_called_once()

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('accounts.tasks.ws_expire_player_invites')
    @mock.patch('accounts.tasks.handle_player_move')
    @mock.patch('accounts.tasks.ws_friend_update_or_create')
    @mock.patch('accounts.tasks.websocket.ws_user_logout')
    def test_watch_user_status_change_offline_with_team(
        self,
        mock_user_logout_ws,
        mock_friend_update,
        mock_lobby_move,
        mock_expire_invites,
    ):
        self.user.add_session()
        self.friend1.add_session()
        lobby = Lobby.create(owner_id=self.friend1.id)
        lobby.start_queue()
        queue()
        team = Team.get_by_lobby_id(lobby.id, fail_silently=True)
        self.assertIsNotNone(team)

        self.friend1.logout()
        tasks.watch_user_status_change(self.friend1.id)

        team = Team.get_by_lobby_id(lobby.id, fail_silently=True)
        self.assertIsNone(team)

        mock_user_logout_ws.assert_called_once()
        mock_friend_update.assert_called_once()
        mock_expire_invites.assert_called_once()
        mock_lobby_move.assert_called_once()

    def test_logout_inactive_users(self):
        self.user.add_session()
        self.user.status = User.Status.ONLINE
        self.user.save()
        yesterday = timezone.now() - datetime.timedelta(days=1, hours=1)
        login = UserLogin.objects.create(user=self.user, ip_address='1.1.1.1')
        login.timestamp = yesterday
        login.save()
        login.refresh_from_db()

        tasks.logout_inactive_users()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, User.Status.OFFLINE)
        self.assertFalse(self.user.is_online)
        self.assertFalse(self.user.has_sessions)
