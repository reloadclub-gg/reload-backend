from unittest import mock

from matchmaking.models import Lobby
from matchmaking.tests.mixins import VerifiedPlayersMixin
from core.tests import TestCase
from websocket import controller


class WSControllerTestCase(VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        return super().setUp()

    @mock.patch('websocket.utils.send_and_close')
    def test_user_status_change_2_online_friends(self, mocker):
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()

        mocker.return_value = True
        controller.user_status_change(self.user_1)
        mocker.assert_awaited()
        self.assertEqual(mocker.await_count, 2)

    @mock.patch('websocket.utils.send_and_close')
    def test_user_status_change_1_online_friend(self, mocker):
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

        mocker.return_value = True
        controller.user_status_change(self.user_1)
        mocker.assert_awaited()
        self.assertEqual(mocker.await_count, 1)

    @mock.patch('websocket.utils.send_and_close')
    def test_user_status_change_no_online_friends(self, mocker):
        self.user_1.auth.add_session()

        mocker.return_value = True
        controller.user_status_change(self.user_1)
        mocker.assert_not_awaited()

    @mock.patch('websocket.utils.send_and_close')
    def test_friendlist_add_2_online_friends(self, mocker):
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()

        mocker.return_value = True
        controller.friendlist_add(self.user_1)
        mocker.assert_awaited()
        self.assertEqual(mocker.await_count, 2)

    @mock.patch('websocket.utils.send_and_close')
    def test_friendlist_add_1_online_friend(self, mocker):
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

        mocker.return_value = True
        controller.friendlist_add(self.user_1)
        mocker.assert_awaited()
        self.assertEqual(mocker.await_count, 1)

    @mock.patch('websocket.utils.send_and_close')
    def test_friendlist_add_no_online_friends(self, mocker):
        self.user_1.auth.add_session()

        mocker.return_value = True
        controller.friendlist_add(self.user_1)
        mocker.assert_not_awaited()

    @mock.patch('websocket.utils.send_and_close')
    def test_lobby_player_invite(self, mocker):
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

        lobby = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        invite = lobby.invite(self.user_1.id, self.user_2.id)

        mocker.return_value = True
        controller.lobby_player_invite(invite)
        mocker.assert_awaited()
        self.assertEqual(mocker.await_count, 1)
