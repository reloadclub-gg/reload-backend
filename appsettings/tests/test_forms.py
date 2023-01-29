from core.tests import TestCase

from ..forms import AppSettingsForm


class AppSettingsFormTestCase(TestCase):
    def test_clean_value_with_kind_integer(self):
        form = AppSettingsForm(data={'name': 'name', 'kind': 'integer', 'value': '1'})

        self.assertTrue(form.is_valid())

    def test_clean_value_with_kind_integer_raised(self):
        form = AppSettingsForm(data={'name': 'name', 'kind': 'integer', 'value': 'A'})

        self.assertFalse(form.is_valid())

    def test_clean_value_with_kind_boolean(self):
        form = AppSettingsForm(data={'name': 'name', 'kind': 'boolean', 'value': '1'})

        self.assertTrue(form.is_valid())

    def test_clean_value_with_kind_boolean_raised(self):
        form = AppSettingsForm(data={'name': 'name', 'kind': 'boolean', 'value': 'A'})

        self.assertFalse(form.is_valid())
