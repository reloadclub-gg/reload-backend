from unittest import mock

from appsettings.models import AppSettings
from core.tests import TestCase


class AppSettingsTestCase(TestCase):
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

    @mock.patch('appsettings.models.ws_maintenance')
    @mock.patch('appsettings.models.ws_create_toast')
    @mock.patch('appsettings.models.Lobby.cancel_all_queues')
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
        mock_ws_create_toast.assert_not_called()
        mock_cancel_queues.assert_called_once()

    @mock.patch('appsettings.models.ws_maintenance')
    @mock.patch('appsettings.models.ws_create_toast')
    @mock.patch('appsettings.models.Lobby.cancel_all_queues')
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
        mock_ws_create_toast.assert_not_called()
        mock_cancel_queues.assert_not_called()
