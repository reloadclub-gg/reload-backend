from django.test import Client
from django.test import TestCase as DjangoTestCase

from core.redis import redis_client_instance as cache


class TestCase(DjangoTestCase):
    def tearDown(self):
        cache.flushdb()
        return super().tearDown()


class APIClient(Client):
    def __init__(self, base_path, *args, **kwargs):
        self.base_path = base_path
        kwargs['raise_request_exception'] = True
        return super().__init__(args, kwargs)

    def build_path(self, path):
        url = ''
        url = self.base_path if self.base_path.endswith('/') else self.base_path + '/'
        url += path[1:] if path.startswith('/') else path
        builded_path = url if url.endswith('/') or '?' in url else url + '/'
        return builded_path

    def call(
        self,
        method,
        path,
        data=None,
        token=None,
        content_type='application/json',
        **extra,
    ):
        if hasattr(self, method):
            req_method = getattr(self, method)
            return req_method(
                path,
                data=data,
                content_type=content_type,
                token=token,
                **extra,
            )

        raise AttributeError(f"{method} isn't a valid method.")

    def generic(
        self,
        method,
        path,
        data="",
        content_type="application/json",
        secure=False,
        **extra,
    ):
        token = extra.get('token')
        path = self.build_path(path)

        return super().generic(
            method,
            path,
            data,
            content_type,
            secure,
            HTTP_AUTHORIZATION=f'Bearer {token}',
            **extra,
        )
