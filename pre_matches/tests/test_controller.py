from unittest import mock

from django.test import override_settings
from model_bakery import baker
from ninja.errors import Http404, HttpError

from core.tests import TestCase
from matches.models import Map, Match, Server

from ..api import controller
from ..models import PreMatch, PreMatchException, Team, TeamException
from . import mixins


class PreMatchControllerTestCase(mixins.TeamsMixin, TestCase):
    @mock.patch('pre_matches.api.controller.ws_update_user')
    @mock.patch('pre_matches.api.controller.ws_match_create')
    def test_handle_create_match(
        self,
        mock_match_create,
        mock_update_user,
    ):
        baker.make(Map)
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )

        for player in pre_match.players[:10]:
            pre_match.set_player_ready(player.id)

        Server.objects.create(ip='123.123.123.123', name='Reload 1')
        match = controller.handle_create_match(pre_match)
        match_player_user1 = self.user_1.matchplayer_set.first()
        match_player_user6 = self.user_6.matchplayer_set.first()
        self.assertIsNotNone(match_player_user1)
        self.assertIsNotNone(match_player_user6)
        self.assertEqual(match_player_user1.team.match, match_player_user6.team.match)

        mock_match_create.assert_called_once_with(match)
        self.assertEqual(mock_update_user.call_count, 10)

    @mock.patch('matches.tasks.send_servers_full_mail.delay')
    @mock.patch('pre_matches.api.controller.ws_update_user')
    @mock.patch('pre_matches.api.controller.ws_match_create')
    def test_handle_create_match_no_server_available(
        self,
        mock_match_create,
        mock_update_user,
        mock_send_mail,
    ):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )

        for player in pre_match.players[:10]:
            pre_match.set_player_ready(player.id)

        match = controller.handle_create_match(pre_match)
        self.assertIsNone(match)

        mock_match_create.assert_not_called()
        mock_update_user.assert_not_called()
        mock_send_mail.assert_called_once()

    @mock.patch('pre_matches.api.controller.ws_update_user')
    @mock.patch('pre_matches.api.controller.websocket.ws_pre_match_delete')
    @mock.patch('pre_matches.api.controller.ws_create_toast')
    def test_handle_create_match_failed(
        self,
        mock_create_toast,
        mock_pre_match_delete,
        mock_update_user,
    ):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )

        for player in pre_match.players[:10]:
            pre_match.set_player_ready(player.id)

        controller.cancel_pre_match(pre_match, 'any message')

        mock_calls = [
            mock.call(self.user_1),
            mock.call(self.user_2),
        ]

        mock_pre_match_delete.assert_called_once()
        self.assertEqual(mock_create_toast.call_count, 10)
        mock_update_user.assert_has_calls(mock_calls)

        with self.assertRaises(PreMatchException):
            PreMatch.get_by_id(pre_match.id)

        with self.assertRaises(TeamException):
            Team.get_by_id(self.team1.id, raise_error=True)
            Team.get_by_id(self.team2.id, raise_error=True)

    def test_handle_pre_match_checks_match_fail(self):
        baker.make(Map)
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        Server.objects.create(ip='123.123.123.123', name='Reload 1')
        controller.handle_create_match(pre_match)

        with self.assertRaises(Http404):
            controller.handle_pre_match_checks(self.user_1, 'error')

    def test_handle_pre_match_checks_pre_match_fail(self):
        with self.assertRaises(Http404):
            controller.handle_pre_match_checks(self.user_1, 'error')

    def test_get_pre_match(self):
        created = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        pre_match = controller.get_pre_match(self.user_1)
        self.assertEqual(created.id, pre_match.id)

    def test_get_pre_match_none(self):
        pre_match = controller.get_pre_match(self.user_1)
        self.assertIsNone(pre_match)

    @mock.patch('pre_matches.api.controller.handle_create_fivem_match')
    @mock.patch('pre_matches.api.controller.websocket.ws_pre_match_update')
    def test_set_player_ready(self, mock_pre_match_update, mock_fivem):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )

        controller.set_player_ready(self.user_1)
        self.assertTrue(self.user_1 in pre_match.players_ready)
        mock_pre_match_update.assert_called_once()
        mock_fivem.assert_not_called()

        with self.assertRaises(HttpError):
            controller.set_player_ready(self.user_1)

    @override_settings(FIVEM_MATCH_MOCK_START_SUCCESS=True)
    @mock.patch('pre_matches.api.controller.mock_fivem_match_start.apply_async')
    @mock.patch('pre_matches.api.controller.handle_create_fivem_match')
    def test_set_player_ready_create_match(self, mock_fivem, mock_match_start):
        baker.make(Map)
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        Server.objects.create(ip='123.123.123.123', name='Reload 1')
        mock_fivem.return_value.status_code = 201
        for player in pre_match.players[:-1]:
            pre_match.set_player_ready(player.id)

        self.assertIsNone(self.user_1.account.get_match())

        controller.set_player_ready(pre_match.players[-1:][0])
        self.user_1.account.refresh_from_db()
        self.assertIsNotNone(self.user_1.account.get_match())
        self.assertEqual(self.user_1.account.get_match().status, Match.Status.WARMUP)
        mock_fivem.assert_called_once()
        mock_match_start.assert_called_once()

    @override_settings(FIVEM_MATCH_MOCK_START_SUCCESS=False)
    @mock.patch('pre_matches.api.controller.mock_fivem_match_cancel.apply_async')
    @mock.patch('pre_matches.api.controller.handle_create_fivem_match')
    def test_set_player_ready_create_match_start_failed(
        self,
        mock_fivem,
        mock_match_cancel,
    ):
        baker.make(Map)
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.mode,
        )
        Server.objects.create(ip='123.123.123.123', name='Reload 1')
        mock_fivem.return_value.status_code = 201
        for player in pre_match.players[:-1]:
            pre_match.set_player_ready(player.id)

        self.assertIsNone(self.user_1.account.get_match())

        controller.set_player_ready(pre_match.players[-1:][0])
        self.user_1.account.refresh_from_db()
        self.assertIsNotNone(self.user_1.account.get_match())
        self.assertEqual(self.user_1.account.get_match().status, Match.Status.WARMUP)
        mock_fivem.assert_called_once()
        mock_match_cancel.assert_called_once()

    @override_settings(
        FIVEM_MATCH_MOCK_DELAY_START=0,
        FIVEM_MATCH_MOCK_DELAY_CONFIGURE=0,
        FIVEM_MATCH_MOCK_CREATION_SUCCESS=True,
    )
    def test_handle_create_fivem_match_success(self):
        server = baker.make(Server)
        match = baker.make(Match, server=server, status=Match.Status.LOADING)
        match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=8, side=2)

        five_response = controller.handle_create_fivem_match(match)
        self.assertEqual(five_response.status_code, 201)

    @override_settings(
        FIVEM_MATCH_MOCK_DELAY_CONFIGURE=0,
        FIVEM_MATCH_MOCK_CREATION_SUCCESS=False,
        FIVEM_MATCH_MOCK_CREATION_MAX_RETRIES=1,
        FIVEM_MATCH_MOCK_CREATION_RETRIES_INTERVAL=0,
    )
    def test_handle_create_fivem_match_error(self):
        server = baker.make(Server)
        match = baker.make(Match, server=server, status=Match.Status.LOADING)
        match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=8, side=2)

        fivem_response = controller.handle_create_fivem_match(match)
        self.assertEqual(fivem_response.status_code, 400)
