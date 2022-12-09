from model_bakery import baker

from core.tests import TestCase


class AppSettingsTestCase(TestCase):
    def test_str(self):
        obj = baker.make('appsettings.AppSettings', name='name')

        self.assertEqual(str(obj), 'name')

    def test_description_isnone(self):
        obj = baker.make('appsettings.AppSettings')

        self.assertIsNone(obj.description)

    def test_obj(self):
        obj = baker.make('appsettings.AppSettings', name='name', value='value',description='description')

        self.assertEqual(obj.name, 'name')
        self.assertEqual(obj.value, 'value')
        self.assertEqual(obj.description, 'description')
