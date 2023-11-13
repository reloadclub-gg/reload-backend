from django.conf import settings

from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase

from ..api import controller, schemas


class StoreControllerTestCase(VerifiedAccountsMixin, TestCase):
    def test_fetch_products(self):
        products = controller.fetch_products()
        self.assertTrue(len(products) > 0)

    def test_start_purchase(self):
        products = controller.fetch_products()

        class Request:
            def build_absolute_uri(self, endpoint: str):
                return settings.FRONT_END_URL + endpoint

        request = Request()
        session_id = controller.start_purchase(
            request,
            schemas.PurchaseSchema.from_orm({'product_id': products[0].id}),
        )
        self.assertIsNotNone(session_id)
