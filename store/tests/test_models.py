from django.core.exceptions import ValidationError
from model_bakery import baker

from accounts.tests.mixins import AccountOneMixin
from core.tests import TestCase

from .. import models


class StoreCommonModelsTestCase(AccountOneMixin, TestCase):
    def test_box_model(self):
        box = baker.make(models.Box, name='Sample Box')
        self.assertEqual(box.handle, 'sample-box')

    def test_collection_model(self):
        collection = baker.make(models.Collection, name='Sample Collection')
        self.assertEqual(collection.handle, 'sample-collection')

    def test_item_model(self):
        item = baker.make(
            models.Item,
            name='Sample Item',
            item_type=models.Item.ItemType.SPRAY,
        )
        self.assertEqual(item.handle, f'{item.item_type}-sample-item')

    def test_item_model_box(self):
        box = baker.make(models.Box, name='Sample Box')
        baker.make(
            models.Item,
            name='Sample Item',
            box=box,
            box_draw_chance=50,
            item_type=models.Item.ItemType.SPRAY,
        )

        baker.make(
            models.Item,
            name='Sample Item 2',
            box=box,
            box_draw_chance=45,
            item_type=models.Item.ItemType.SPRAY,
        )

        with self.assertRaises(ValidationError):
            baker.make(
                models.Item,
                name='Sample Item 3',
                box=box,
                box_draw_chance=10,
                item_type=models.Item.ItemType.SPRAY,
            )

        baker.make(
            models.Item,
            name='Sample Item 3',
            box=box,
            box_draw_chance=5,
            item_type=models.Item.ItemType.SPRAY,
        )

    def test_decorative_item(self):
        item = models.Item(
            name='Sample Item',
            item_type=models.Item.ItemType.DECORATIVE,
            subtype=models.Item.SubType.CARD,
            price=5,
            description='desc',
        )
        item.decorative_image = 'decorative-card-item.png'
        item.save()
