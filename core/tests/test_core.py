from . import APIClient, TestCase, cache


class CoreTestCaseTestCase(TestCase):
    def test_test_case_flush_cache_on_tear_down(self):
        cache.set('one', 1)
        cache.set('two', 3)
        cache.set('three', 3)

        self.tearDown()
        keys = cache.keys('*')
        self.assertEqual(len(keys), 0)


class CoreApiClientTestCase(TestCase):
    def test_build_path(self):
        base_path = '/api/accounts'
        expected_path = '/api/accounts/any/'
        client = APIClient(base_path)

        path = client.build_path('any')
        self.assertEqual(path, expected_path)

        path = client.build_path('/any')
        self.assertEqual(path, expected_path)

        path = client.build_path('any/')
        self.assertEqual(path, expected_path)

        path = client.build_path('/any/')
        self.assertEqual(path, expected_path)

        expected_path = '/api/accounts/any/one/'

        path = client.build_path('any/one')
        self.assertEqual(path, expected_path)

    def test_call(self):
        client = APIClient('/api')
        with self.assertRaises(AttributeError):
            client.call('inexistent', 'any')

        call = client.generic('get', '', token='token')
        self.assertEqual(
            call.headers.get('Content-Type'), 'application/json; charset=utf-8'
        )
        self.assertEqual(call.request.get('token'), 'token')

    def test_i18n(self):
        client = APIClient('/api')
        r = client.generic(
            'get', '', HTTP_ACCEPT_LANGUAGE='pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        )
        self.assertEqual(r.json().get('language'), 'pt-br')
        self.assertEqual(
            r.json().get('i18n_check'), 'A internacionalização está funcionando.'
        )
