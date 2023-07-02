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
