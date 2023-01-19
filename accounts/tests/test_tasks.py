from unittest import mock

from core.tests import TestCase
from matchmaking.models import Lobby

from .. import tasks
from . import mixins


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
        self.user.auth.add_session()
        Lobby.create(owner_id=self.user.id)
        self.user.auth.expire_session(seconds=0)
        tasks.watch_user_status_change(self.user.id)
        mock_quit.assert_called_once()
