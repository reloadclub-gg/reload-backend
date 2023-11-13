from django.conf import settings
from stripe.error import AuthenticationError

from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase

from ..api import controller, schemas


class StoreControllerTestCase(VerifiedAccountsMixin, TestCase):
    def test_fetch_products(self):
        if not settings.STRIPE_PUBLIC_KEY or not settings.STRIPE_SECRET_KEY:
            with self.assertRaises(AuthenticationError):
                products = controller.fetch_products()
        else:
            products = controller.fetch_products()
            self.assertTrue(len(products) > 0)

    def test_start_purchase(self):
        if not settings.STRIPE_PUBLIC_KEY or not settings.STRIPE_SECRET_KEY:
            with self.assertRaises(AuthenticationError):
                products = controller.fetch_products()
        else:
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
