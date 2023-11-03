from unittest import mock

from django.test import override_settings

from appsettings.models import AppSettings
from core.tests import TestCase
from pre_matches.models import PreMatch, Team
from pre_matches.tests.mixins import LobbiesMixin


class AppSettingsTestCase(LobbiesMixin, TestCase):
    def test_get_str(self):
        config = AppSettings(name='name', kind=AppSettings.TEXT, value='test')
        config.save()
        value = AppSettings.get('name')
        self.assertTrue(isinstance(value, str))
        self.assertEqual(value, 'test')

    def test_get_bool(self):
        config = AppSettings(name='name', kind=AppSettings.BOOLEAN, value="0")
        config.save()
        value = AppSettings.get('name')
        self.assertTrue(isinstance(value, bool))
        self.assertEqual(value, False)

    def test_get_int(self):
        config = AppSettings(name='name', kind=AppSettings.INTEGER, value="5")
        config.save()
        value = AppSettings.get('name')
        self.assertTrue(isinstance(value, int))
        self.assertEqual(value, 5)

    @mock.patch('appsettings.signals.ws_maintenance')
    @mock.patch('appsettings.signals.ws_create_toast')
    @mock.patch('appsettings.signals.Lobby.cancel_all_queues')
    def test_update_maintanence_start(
        self,
        mock_cancel_queues,
        mock_ws_create_toast,
        mock_ws_maintanence,
    ):
        maintanence = AppSettings.objects.get(name='Maintenance Window')
        maintanence.value = '1'
        maintanence.save()

        mock_ws_maintanence.assert_called_once_with('start')
        mock_ws_create_toast.assert_called_once()
        mock_cancel_queues.assert_called_once()

    @mock.patch('appsettings.signals.ws_maintenance')
    @mock.patch('appsettings.signals.ws_create_toast')
    @mock.patch('appsettings.signals.Lobby.cancel_all_queues')
    def test_update_maintanence_end(
        self,
        mock_cancel_queues,
        mock_ws_create_toast,
        mock_ws_maintanence,
    ):
        maintanence = AppSettings.objects.get(name='Maintenance Window')
        maintanence.value = '0'
        maintanence.save()

        mock_ws_maintanence.assert_called_once_with('end')
        mock_ws_create_toast.assert_called_once()
        mock_cancel_queues.assert_not_called()

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('appsettings.signals.ws_maintenance')
    @mock.patch('appsettings.signals.ws_create_toast')
    @mock.patch('appsettings.signals.Lobby.cancel_all_queues')
    def test_update_maintanence_start_with_team(
        self,
        mock_cancel_queues,
        mock_ws_create_toast,
        mock_ws_maintanence,
    ):
        self.lobby1.start_queue()
        team = Team.create([self.lobby1.id])
        self.assertIsNotNone(team)

        maintanence = AppSettings.objects.get(name='Maintenance Window')
        maintanence.value = '1'
        maintanence.save()

        team = Team.get_by_lobby_id(self.lobby1.id, fail_silently=True)
        self.assertIsNone(team)

        mock_ws_maintanence.assert_called_once_with('start')
        mock_ws_create_toast.assert_called_once()
        mock_cancel_queues.assert_called_once()

    @override_settings(TEAM_READY_PLAYERS_MIN=1)
    @mock.patch('appsettings.signals.cancel_pre_match')
    @mock.patch('appsettings.signals.ws_maintenance')
    @mock.patch('appsettings.signals.ws_create_toast')
    @mock.patch('appsettings.signals.Lobby.cancel_all_queues')
    def test_update_maintanence_start_with_pre_match(
        self,
        mock_cancel_queues,
        mock_ws_create_toast,
        mock_ws_maintanence,
        mock_cancel_pre_match,
    ):
        self.lobby1.start_queue()
        self.lobby2.start_queue()
        t1 = Team.create([self.lobby1.id])
        t2 = Team.create([self.lobby2.id])
        pm = PreMatch.create(t1.id, t2.id, self.lobby1.lobby_type, self.lobby1.mode)

        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        self.assertIsNotNone(pm)

        maintanence = AppSettings.objects.get(name='Maintenance Window')
        maintanence.value = '1'
        maintanence.save()

        t1 = Team.get_by_lobby_id(self.lobby1.id, fail_silently=True)
        t2 = Team.get_by_lobby_id(self.lobby2.id, fail_silently=True)
        self.assertIsNone(t1)
        self.assertIsNone(t2)

        pm = PreMatch.get_by_player_id(self.user_1.id)
        self.assertIsNone(pm)
        pm = PreMatch.get_by_player_id(self.user_2.id)
        self.assertIsNone(pm)

        mock_ws_maintanence.assert_called_once_with('start')
        mock_ws_create_toast.assert_called_once()
        mock_cancel_queues.assert_called_once()
        mock_cancel_pre_match.assert_called_once()
