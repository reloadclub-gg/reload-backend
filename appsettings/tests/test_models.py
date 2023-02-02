from model_bakery import baker

from appsettings.models import AppSettings
from core.tests import TestCase


class AppSettingsTestCase(TestCase):
    def test_str(self):
        obj = baker.make(AppSettings, name='name')

        self.assertEqual(str(obj), 'name')

    def test_description_isnone(self):
        obj = baker.make(AppSettings)

        self.assertIsNone(obj.description)

    def test_obj(self):
        obj = baker.make(
            AppSettings,
            name='name',
            value='value',
            description='description',
        )

        self.assertEqual(obj.name, 'name')
        self.assertEqual(obj.value, 'value')
        self.assertEqual(obj.description, 'description')

    def test_get(self):
        AppSettings.objects.create(kind=AppSettings.TEXT, name='name', value='test')
        config = AppSettings.get('name')
        self.assertEqual(config, 'test')

    def test_set_text(self):
        AppSettings.set_text(name='name', value='test')
        config = AppSettings.get('name')
        self.assertEqual(config, 'test')

    def test_set_boolean(self):
        AppSettings.set_bool(name='name', value=True)
        config = AppSettings.get('name')
        self.assertEqual(config, True)

        AppSettings.set_bool(name='name2', value=False)
        config = AppSettings.get('name2')
        self.assertEqual(config, False)

    def test_set_int(self):
        AppSettings.set_int(name='name', value=1)
        config = AppSettings.get('name')
        self.assertEqual(config, 1)

        AppSettings.set_int(name='name2', value=3)
        config = AppSettings.get('name2')
        self.assertEqual(config, 3)

    def test_save(self):
        config = AppSettings(name='name', kind=AppSettings.TEXT, value='test')
        config.save()
        value = AppSettings.get('name')
        self.assertEqual(value, 'test')

        config = AppSettings(name='name2', kind=AppSettings.BOOLEAN, value=False)
        config.save()
        value = AppSettings.get('name2')
        self.assertEqual(value, False)

        config = AppSettings(name='name3', kind=AppSettings.INTEGER, value=5)
        config.save()
        value = AppSettings.get('name3')
        self.assertEqual(value, 5)
