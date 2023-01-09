import asyncio
from unittest import mock

from matchmaking.tests.mixins import VerifiedPlayersMixin
from core.tests import TestCase
from websocket.controller import user_status_change


class WSControllerTestCase(VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        return super().setUp()

    @mock.patch('websocket.utils.send_and_close')
    def test_user_status_change_2_online_friends(self, mocker):
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()

        mocker.return_value = True
        user_status_change(self.user_1)
        mocker.assert_awaited()
        self.assertEqual(mocker.await_count, 2)

    @mock.patch('websocket.utils.send_and_close')
    def test_user_status_change_1_online_friend(self, mocker):
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

        mocker.return_value = True
        user_status_change(self.user_1)
        mocker.assert_awaited()
        self.assertEqual(mocker.await_count, 1)

    @mock.patch('websocket.utils.send_and_close')
    def test_user_status_change_no_online_friend(self, mocker):
        self.user_1.auth.add_session()

        mocker.return_value = True
        user_status_change(self.user_1)
        mocker.assert_not_awaited()
