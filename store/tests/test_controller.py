from django.conf import settings
from model_bakery import baker
from ninja.errors import HttpError
from stripe.error import AuthenticationError

from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase

from .. import models
from ..api import controller, schemas


class StoreControllerTestCase(VerifiedAccountsMixin, TestCase):
    def test_fetch_products(self):
        if not settings.STRIPE_PUBLIC_KEY or not settings.STRIPE_SECRET_KEY:
            with self.assertRaises(AuthenticationError):
                products = controller.fetch_products()
        else:
            products = controller.fetch_products()
            self.assertTrue(len(products) > 0)

    def test_buy_product(self):
        if not settings.STRIPE_PUBLIC_KEY or not settings.STRIPE_SECRET_KEY:
            with self.assertRaises(AuthenticationError):
                products = controller.fetch_products()
        else:
            products = controller.fetch_products()

            class Request:
                def build_absolute_uri(self, endpoint: str):
                    return settings.FRONT_END_URL + endpoint

            request = Request()
            request.user = self.user_1
            session_id = controller.buy_product(
                request,
                schemas.PurchaseSchema.from_orm({'product_id': products[0].id}),
            )
            self.assertIsNotNone(session_id)

    def test_purchase_item(self):
        item = baker.make(
            models.Item,
            price=500,
            is_available=True,
            name='i1',
            item_type=models.Item.ItemType.SPRAY,
        )
        self.user_1.account.coins = 1000
        self.user_1.account.save()

        self.assertFalse(self.user_1.useritem_set.filter(item__id=item.id).exists())
        new_coins = self.user_1.account.coins - item.price
        controller.purchase_item(self.user_1, item.id)
        self.assertTrue(self.user_1.useritem_set.filter(item__id=item.id).exists())
        self.assertEqual(self.user_1.account.coins, new_coins)

        item = baker.make(
            models.Item,
            price=2000,
            is_available=True,
            name='i2',
            item_type=models.Item.ItemType.SPRAY,
        )
        with self.assertRaisesMessage(HttpError, 'Insufficient funds.'):
            controller.purchase_item(self.user_1, item.id)
        self.assertFalse(self.user_1.useritem_set.filter(item__id=item.id).exists())
        self.assertEqual(self.user_1.account.coins, new_coins)

        item = baker.make(
            models.Item,
            price=1,
            is_available=False,
            name='i3',
            item_type=models.Item.ItemType.SPRAY,
        )
        with self.assertRaisesMessage(HttpError, 'Item not available.'):
            controller.purchase_item(self.user_1, item.id)
        self.assertFalse(self.user_1.useritem_set.filter(item__id=item.id).exists())
        self.assertEqual(self.user_1.account.coins, new_coins)

    def test_purchase_item_unique(self):
        item = baker.make(
            models.Item,
            price=500,
            is_available=True,
            name='i1',
            item_type=models.Item.ItemType.SPRAY,
        )
        self.user_1.account.coins = 1000
        self.user_1.account.save()
        new_coins = self.user_1.account.coins - item.price
        controller.purchase_item(self.user_1, item.id)
        self.assertEqual(self.user_1.account.coins, new_coins)
        with self.assertRaisesMessage(HttpError, 'Cannot process purchase.'):
            controller.purchase_item(self.user_1, item.id)
        self.user_1.account.refresh_from_db()
        self.assertEqual(self.user_1.account.coins, new_coins)

    def test_purchase_box(self):
        box = baker.make(models.Box, price=500, is_available=True, name='b1')
        self.user_1.account.coins = 1000
        self.user_1.account.save()

        self.assertFalse(self.user_1.userbox_set.filter(box__id=box.id).exists())
        new_coins = self.user_1.account.coins - box.price
        controller.purchase_box(self.user_1, box.id)
        self.assertTrue(self.user_1.userbox_set.filter(box__id=box.id).exists())
        self.assertEqual(self.user_1.account.coins, new_coins)

        box = baker.make(models.Box, price=2000, is_available=True, name='b2')
        with self.assertRaisesMessage(HttpError, 'Insufficient funds.'):
            controller.purchase_box(self.user_1, box.id)
        self.assertFalse(self.user_1.userbox_set.filter(box__id=box.id).exists())
        self.assertEqual(self.user_1.account.coins, new_coins)

        box = baker.make(models.Box, price=1, is_available=False, name='b3')
        with self.assertRaisesMessage(HttpError, 'Item not available.'):
            controller.purchase_box(self.user_1, box.id)
        self.assertFalse(self.user_1.userbox_set.filter(box__id=box.id).exists())
        self.assertEqual(self.user_1.account.coins, new_coins)

    def test_purchase_box_unique(self):
        box = baker.make(models.Box, price=500, is_available=True, name='b1')
        self.user_1.account.coins = 1000
        self.user_1.account.save()
        new_coins = self.user_1.account.coins - box.price
        controller.purchase_box(self.user_1, box.id)
        self.assertEqual(self.user_1.account.coins, new_coins)
        with self.assertRaisesMessage(HttpError, 'Cannot process purchase.'):
            controller.purchase_box(self.user_1, box.id)
        self.user_1.account.refresh_from_db()
        self.assertEqual(self.user_1.account.coins, new_coins)

    def test_purchase_collection(self):
        collection = baker.make(
            models.Collection,
            price=500,
            is_available=True,
            name='c1',
        )
        baker.make(
            models.Item,
            price=500,
            is_available=True,
            name='i1',
            collection=collection,
            item_type=models.Item.ItemType.SPRAY,
        )
        baker.make(
            models.Item,
            price=500,
            is_available=True,
            name='i2',
            collection=collection,
            item_type=models.Item.ItemType.SPRAY,
        )
        baker.make(
            models.Item,
            price=500,
            is_available=True,
            name='i3',
            collection=collection,
            item_type=models.Item.ItemType.SPRAY,
        )
        self.user_1.account.coins = 1000
        self.user_1.account.save()

        for item in collection.item_set.all():
            self.assertFalse(self.user_1.useritem_set.filter(item__id=item.id).exists())
        new_coins = self.user_1.account.coins - collection.price
        controller.purchase_collection(self.user_1, collection.id)
        self.assertEqual(self.user_1.account.coins, new_coins)
        for item in collection.item_set.all():
            self.assertTrue(self.user_1.useritem_set.filter(item__id=item.id).exists())

        collection = baker.make(
            models.Collection,
            price=2000,
            is_available=True,
            name='c2',
        )
        with self.assertRaisesMessage(HttpError, 'Insufficient funds.'):
            controller.purchase_collection(self.user_1, collection.id)
        for item in collection.item_set.all():
            self.assertFalse(self.user_1.useritem_set.filter(item__id=item.id).exists())
        self.assertEqual(self.user_1.account.coins, new_coins)

        collection = baker.make(
            models.Collection,
            price=1,
            is_available=False,
            name='c3',
        )
        with self.assertRaisesMessage(HttpError, 'Item not available.'):
            controller.purchase_collection(self.user_1, collection.id)
        for item in collection.item_set.all():
            self.assertFalse(self.user_1.useritem_set.filter(item__id=item.id).exists())
        self.assertEqual(self.user_1.account.coins, new_coins)

    def test_purchase_collection_unique(self):
        collection = baker.make(
            models.Collection,
            price=500,
            is_available=True,
            name='c1',
        )
        baker.make(
            models.Item,
            price=500,
            is_available=True,
            name='i1',
            collection=collection,
            item_type=models.Item.ItemType.SPRAY,
        )
        baker.make(
            models.Item,
            price=500,
            is_available=True,
            name='i2',
            collection=collection,
            item_type=models.Item.ItemType.SPRAY,
        )
        baker.make(
            models.Item,
            price=500,
            is_available=True,
            name='i3',
            collection=collection,
            item_type=models.Item.ItemType.SPRAY,
        )
        self.user_1.account.coins = 1000
        self.user_1.account.save()
        new_coins = self.user_1.account.coins - collection.price

        controller.purchase_collection(self.user_1, collection.id)
        self.assertEqual(self.user_1.account.coins, new_coins)
        with self.assertRaisesMessage(HttpError, 'Cannot process purchase.'):
            controller.purchase_collection(self.user_1, collection.id)
        self.user_1.account.refresh_from_db()
        self.assertEqual(self.user_1.account.coins, new_coins)

        with self.assertRaisesMessage(HttpError, 'Cannot process purchase.'):
            controller.purchase_collection(self.user_1, collection.id)
        self.user_1.account.refresh_from_db()
        self.assertEqual(self.user_1.account.coins, new_coins)
