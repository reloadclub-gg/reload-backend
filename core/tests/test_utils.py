from ninja import Schema

from . import TestCase
from .. import utils


class RequestSchema1(Schema):
    META: dict = {
        'HTTP_X_FORWARDED_FOR': '111.111.111.111'
    }


class RequestSchema2(Schema):
    META: dict = {
        'REMOTE_ADDR': '222.222.222.222'
    }


class CoreUtilsTestCase(TestCase):

    def test_generate_random_string_length(self):
        str = utils.generate_random_string()
        self.assertEqual(len(str), 6)

        str = utils.generate_random_string(4)
        self.assertEqual(len(str), 4)

    def test_generate_random_string_type(self):
        str = utils.generate_random_string(allowed_chars='letters')
        self.assertFalse(str.isdigit())
        self.assertFalse(any(char.isdigit() for char in str))

        str = utils.generate_random_string(allowed_chars='digits')
        self.assertTrue(str.isdigit())
        self.assertTrue(any(char.isdigit() for char in str))

    def test_get_ip_address(self):
        ip = utils.get_ip_address(RequestSchema1())
        self.assertEqual(ip, '111.111.111.111')

        ip = utils.get_ip_address(RequestSchema2())
        self.assertEqual(ip, '222.222.222.222')

    def test_get_url_param(self):
        url = 'anyurl.com/?key=1'
        value = utils.get_url_param(url, 'key')
        self.assertEqual(value, '1')

        url = b'anyurl.com/?key=2'
        value = utils.get_url_param(url, 'key')
        self.assertEqual(value, '2')

        url = '?key=3'
        value = utils.get_url_param(url, 'key')
        self.assertEqual(value, '3')

        url = 'key=4'
        value = utils.get_url_param(url, 'key')
        self.assertEqual(value, '4')

        url = b'key=5'
        value = utils.get_url_param(url, 'key')
        self.assertEqual(value, '5')
