import tempfile

from model_bakery import baker

from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import APIClient, TestCase

from .. import models


class StoreRoutesTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient('/api/store')
        self.user_1.auth.create_token()

        self.tmp_image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        self.item = baker.make(
            models.Item,
            name='Test Item',
            foreground_image=self.tmp_image,
            cover_image=self.tmp_image,
            price=9.90,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )
        self.box = baker.make(
            models.Box,
            name='Test Box',
            foreground_image=self.tmp_image,
            cover_image=self.tmp_image,
            price=9.90,
            is_available=True,
        )
        self.collection = baker.make(
            models.Collection,
            name='Test Collection',
            foreground_image=self.tmp_image,
            cover_image=self.tmp_image,
            price=9.90,
            is_available=True,
        )
        self.box_item = baker.make(
            models.Item,
            box=self.box,
            name='Test Box Item',
            foreground_image=self.tmp_image,
            cover_image=self.tmp_image,
            price=9.90,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )
        self.collection_item = baker.make(
            models.Item,
            collection=self.collection,
            name='Test Collection Item',
            foreground_image=self.tmp_image,
            cover_image=self.tmp_image,
            price=9.90,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )

    def test_inventory_list(self):
        r = self.api.call(
            'get',
            '/inventory',
            token=self.user_1.auth.token,
        )
        self.assertEqual(len(r.json().get('items')), 0)
        self.assertEqual(len(r.json().get('boxes')), 0)

        baker.make(models.UserItem, item=self.item, user=self.user_1)
        baker.make(models.UserBox, box=self.box, user=self.user_1)

        r = self.api.call(
            'get',
            '/inventory',
            token=self.user_1.auth.token,
        )
        self.assertEqual(len(r.json().get('items')), 1)
        self.assertEqual(len(r.json().get('boxes')), 1)

    def test_item_update(self):
        user_item = baker.make(models.UserItem, item=self.item, user=self.user_1)
        r = self.api.call(
            'patch',
            f'/inventory/{user_item.id}',
            token=self.user_1.auth.token,
            data={'in_use': True},
        )
        self.assertTrue(r.json().get('items')[0].get('in_use'))

        r = self.api.call(
            'patch',
            f'/inventory/{user_item.id}',
            token=self.user_1.auth.token,
            data={'in_use': False},
        )
        self.assertFalse(r.json().get('items')[0].get('in_use'))

        item_1 = baker.make(
            models.Item,
            name='Spray 1',
            foreground_image=self.tmp_image,
            cover_image=self.tmp_image,
            price=9.90,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )

        item_2 = baker.make(
            models.Item,
            name='Spray 2',
            foreground_image=self.tmp_image,
            cover_image=self.tmp_image,
            price=9.90,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )

        user_item_1 = baker.make(
            models.UserItem,
            item=item_1,
            user=self.user_1,
            can_use=True,
            in_use=False,
        )
        user_item_2 = baker.make(
            models.UserItem,
            item=item_2,
            user=self.user_1,
            can_use=True,
            in_use=False,
        )

        r = self.api.call(
            'patch',
            f'/inventory/{user_item_1.id}',
            token=self.user_1.auth.token,
            data={'in_use': True},
        )
        count = sum(bool(d.get('in_use')) for d in r.json().get('items'))
        self.assertEqual(count, 1)

        r = self.api.call(
            'patch',
            f'/inventory/{user_item_2.id}',
            token=self.user_1.auth.token,
            data={'in_use': True},
        )
        count = sum(bool(d.get('in_use')) for d in r.json().get('items'))
        self.assertEqual(count, 1)
