import tempfile
from datetime import timedelta

from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from model_bakery import baker

from accounts.tests.mixins import AccountOneMixin
from appsettings.models import AppSettings
from core.redis import redis_client_instance as cache
from core.tests import TestCase
from core.utils import get_full_file_path, str_to_timezone

from .. import models
from ..api import controller, schemas


class StoreSchemaTestCase(AccountOneMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tmp_image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        self.item = baker.make(
            models.Item,
            name='Test Item',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )
        self.box = baker.make(
            models.Box,
            name='Test Box',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
        )
        self.collection = baker.make(
            models.Collection,
            name='Test Collection',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
        )
        self.box_item = baker.make(
            models.Item,
            box=self.box,
            name='Test Box Item',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )
        self.collection_item = baker.make(
            models.Item,
            collection=self.collection,
            name='Test Collection Item',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )

    def tearDown(self):
        tempfile.mkstemp()
        super().tearDown()

    def test_item_schema(self):
        payload = schemas.ItemSchema.from_orm(self.item).dict()
        expected_payload = {
            'id': self.item.id,
            'name': self.item.name,
            'item_type': self.item.item_type,
            'subtype': self.item.subtype,
            'handle': self.item.handle,
            'price': self.item.price,
            'release_date': self.item.release_date,
            'description': self.item.description,
            'discount': self.item.discount,
            'background_image': get_full_file_path(self.item.background_image)
            if self.item.background_image
            else None,
            'foreground_image': get_full_file_path(self.item.foreground_image),
            'featured_image': get_full_file_path(self.item.featured_image),
            'decorative_image': get_full_file_path(self.item.decorative_image)
            if self.item.decorative_image
            else None,
            'box_id': schemas.BoxSchema.from_orm(self.item.box)
            if self.item.box
            else None,
            'box_draw_chance': self.item.box_draw_chance,
            'collection_id': schemas.CollectionSchema.from_orm(self.collection)
            if self.item.collection
            else None,
            'featured': self.item.featured,
            'in_use': None,
            'can_use': None,
            'object': 'item',
            'media': [],
        }
        self.assertEqual(payload, expected_payload)

    def test_item_media_schema(self):
        baker.make(models.ItemMedia, item=self.item, file=self.tmp_image, _quantity=4)
        payload = schemas.ItemSchema.from_orm(self.item).dict()
        expected_payload = {
            'id': self.item.id,
            'name': self.item.name,
            'item_type': self.item.item_type,
            'subtype': self.item.subtype,
            'handle': self.item.handle,
            'price': self.item.price,
            'release_date': self.item.release_date,
            'description': self.item.description,
            'discount': self.item.discount,
            'background_image': get_full_file_path(self.item.background_image)
            if self.item.background_image
            else None,
            'foreground_image': get_full_file_path(self.item.foreground_image),
            'featured_image': get_full_file_path(self.item.featured_image),
            'decorative_image': get_full_file_path(self.item.decorative_image)
            if self.item.decorative_image
            else None,
            'box_id': self.item.box.id if self.item.box else None,
            'box_draw_chance': self.item.box_draw_chance,
            'collection_id': self.collection.id if self.item.collection else None,
            'featured': self.item.featured,
            'in_use': None,
            'can_use': None,
            'object': 'item',
            'media': [
                schemas.ItemMediaSchema.from_orm(media)
                for media in self.item.itemmedia_set.all()
            ],
        }
        self.assertEqual(payload, expected_payload)
        self.assertTrue('http' in payload.get('media')[0].get('file'))

    def test_item_box_schema(self):
        payload = schemas.ItemSchema.from_orm(self.box_item).dict()
        expected_payload = {
            'id': self.box_item.id,
            'name': self.box_item.name,
            'item_type': self.box_item.item_type,
            'subtype': self.box_item.subtype,
            'handle': self.box_item.handle,
            'price': self.box_item.price,
            'release_date': self.box_item.release_date,
            'description': self.box_item.description,
            'discount': self.box_item.discount,
            'background_image': get_full_file_path(self.box_item.background_image)
            if self.box_item.background_image
            else None,
            'foreground_image': get_full_file_path(self.box_item.foreground_image),
            'featured_image': get_full_file_path(self.box_item.featured_image),
            'decorative_image': get_full_file_path(self.box_item.decorative_image)
            if self.box_item.decorative_image
            else None,
            'box_id': self.box.id,
            'box_draw_chance': self.box_item.box_draw_chance,
            'collection_id': self.collection.id if self.box_item.collection else None,
            'featured': self.box_item.featured,
            'in_use': None,
            'can_use': None,
            'object': 'item',
            'media': [],
        }
        self.assertEqual(payload, expected_payload)

    def test_item_collection_schema(self):
        payload = schemas.ItemSchema.from_orm(self.collection_item).dict()
        expected_payload = {
            'id': self.collection_item.id,
            'name': self.collection_item.name,
            'item_type': self.collection_item.item_type,
            'subtype': self.collection_item.subtype,
            'handle': self.collection_item.handle,
            'price': self.collection_item.price,
            'release_date': self.collection_item.release_date,
            'description': self.collection_item.description,
            'discount': self.collection_item.discount,
            'background_image': get_full_file_path(
                self.collection_item.background_image
            )
            if self.collection_item.background_image
            else None,
            'foreground_image': get_full_file_path(
                self.collection_item.foreground_image
            ),
            'featured_image': get_full_file_path(self.collection_item.featured_image),
            'decorative_image': get_full_file_path(
                self.collection_item.decorative_image
            )
            if self.collection_item.decorative_image
            else None,
            'box_id': self.item.box.id if self.item.box else None,
            'box_draw_chance': self.collection_item.box_draw_chance,
            'collection_id': self.collection.id,
            'featured': self.collection_item.featured,
            'in_use': None,
            'can_use': None,
            'object': 'item',
            'media': [],
        }
        self.assertEqual(payload, expected_payload)

    def test_box_schema(self):
        payload = schemas.BoxSchema.from_orm(self.box).dict()
        expected_payload = {
            'id': self.box.id,
            'name': self.box.name,
            'handle': self.box.handle,
            'price': self.box.price,
            'release_date': self.box.release_date,
            'description': self.box.description,
            'discount': self.box.discount,
            'background_image': get_full_file_path(self.box.background_image)
            if self.box.background_image
            else None,
            'foreground_image': get_full_file_path(self.box.foreground_image),
            'featured_image': get_full_file_path(self.box.featured_image),
            'featured': self.box.featured,
            'can_open': None,
            'object': 'box',
            'items': [
                schemas.ItemSchema.from_orm(item)
                for item in self.box.item_set.filter(is_available=True)
            ],
        }
        self.assertEqual(payload, expected_payload)

    def test_collection_schema(self):
        payload = schemas.CollectionSchema.from_orm(self.collection).dict()
        expected_payload = {
            'id': self.collection.id,
            'name': self.collection.name,
            'handle': self.collection.handle,
            'price': self.collection.price,
            'release_date': self.collection.release_date,
            'description': self.collection.description,
            'discount': self.collection.discount,
            'background_image': get_full_file_path(self.collection.background_image)
            if self.box.background_image
            else None,
            'foreground_image': get_full_file_path(self.collection.foreground_image),
            'featured_image': get_full_file_path(self.collection.featured_image),
            'featured': self.collection.featured,
            'object': 'collection',
            'items': [
                schemas.ItemSchema.from_orm(item)
                for item in self.collection.item_set.filter(is_available=True)
            ],
        }
        self.assertEqual(payload, expected_payload)

    def test_user_inventory_schema(self):
        payload = schemas.UserInventorySchema.from_orm(self.user).dict()
        expected_payload = {
            'id': f'{self.user.email}{self.user.id}inventory',
            'user_id': self.user.id,
            'items': [],
            'boxes': [],
        }

        self.assertEqual(payload, expected_payload)

        payload = schemas.UserInventorySchema.from_orm(self.user).dict()
        expected_payload = {
            'id': f'{self.user.email}{self.user.id}inventory',
            'user_id': self.user.id,
            'items': [
                schemas.UserItemSchema.from_orm(user_item)
                for user_item in models.UserItem.objects.filter(user=self.user)
            ],
            'boxes': [],
        }
        self.assertEqual(payload, expected_payload)

        payload = schemas.UserInventorySchema.from_orm(self.user).dict()
        expected_payload = {
            'id': f'{self.user.email}{self.user.id}inventory',
            'user_id': self.user.id,
            'items': [
                schemas.UserItemSchema.from_orm(user_item)
                for user_item in models.UserItem.objects.filter(user=self.user)
            ],
            'boxes': [
                schemas.UserBoxSchema.from_orm(user_box)
                for user_box in models.UserBox.objects.filter(user=self.user)
            ],
        }

        self.assertEqual(payload, expected_payload)

    def test_user_store_schema(self):
        item0 = baker.make(
            models.Item,
            name='Test Item 0',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
            item_type=models.Item.ItemType.SPRAY,
        )

        payload = controller.get_user_store(self.user).dict()
        self.assertEqual(len(payload.get('products')), 5)
        self.assertEqual(payload.get('id'), f'{self.user.email}{self.user.id}store')
        self.assertEqual(payload.get('user_id'), self.user.id)

        baker.make(models.UserItem, item=self.item, user=self.user)
        payload = controller.get_user_store(self.user).dict()
        self.assertEqual(len(payload.get('products')), 5)

        AppSettings.objects.create(
            name='Replaceable Store Items',
            kind=AppSettings.BOOLEAN,
            value='1',
        )

        baker.make(models.UserItem, item=item0, user=self.user)
        payload = controller.get_user_store(self.user).dict()
        self.assertEqual(len(payload.get('products')), 3)

        self.assertEqual(len(payload.get('featured')), 0)
        baker.make(
            models.Item,
            name='Test Item Featured',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
            featured=True,
            item_type=models.Item.ItemType.SPRAY,
        )
        payload = controller.get_user_store(self.user).dict()
        self.assertEqual(len(payload.get('featured')), 1)

        baker.make(
            models.Item,
            name='Test Item 2',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=False,
            featured=True,
            item_type=models.Item.ItemType.SPRAY,
        )

        payload = controller.get_user_store(self.user).dict()
        self.assertEqual(len(payload.get('products')), 3)
        self.assertEqual(len(payload.get('featured')), 1)

        baker.make(
            models.Box,
            name='Feat Box',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
            featured=True,
        )

        baker.make(
            models.Collection,
            name='Feat Collection',
            foreground_image=self.tmp_image,
            featured_image=self.tmp_image,
            price=9,
            is_available=True,
            featured=True,
        )

        payload = controller.get_user_store(self.user).dict()
        self.assertEqual(len(payload.get('products')), 3)
        self.assertEqual(len(payload.get('featured')), 3)

    @override_settings(STORE_LENGTH=2)
    def test_user_store_schema_length(self):
        payload = controller.get_user_store(self.user).dict()
        self.assertEqual(len(payload.get('products')), 2)

    @override_settings(STORE_LENGTH=1)
    def test_user_store_schema_rotation(self):
        payload = controller.get_user_store(self.user).dict()
        product1 = payload.get('products')[0]
        self.assertEqual(len(payload.get('products')), 1)

        payload = controller.get_user_store(self.user).dict()
        product2 = payload.get('products')[0]
        self.assertEqual(len(payload.get('products')), 1)
        self.assertEqual(product1.get('id'), product2.get('id'))

        cache.delete(f'__store:user:{self.user.id}:last_updated')
        cache.delete(f'__store:user:{self.user.id}:items')
        cache.delete(f'__store:user:{self.user.id}:boxes')

        payload = controller.get_user_store(self.user).dict()
        self.assertEqual(len(payload.get('products')), 1)
        next_rotation_date = str_to_timezone(payload.get('next_rotation'))
        expected_rotation_date = timezone.now() + timedelta(
            days=settings.STORE_ROTATION_DAYS
        )
        self.assertEqual(next_rotation_date.day, expected_rotation_date.day)
        self.assertEqual(next_rotation_date.hour, expected_rotation_date.hour)
