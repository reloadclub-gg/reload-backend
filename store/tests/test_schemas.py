import tempfile
from decimal import Decimal

from django.test import override_settings
from model_bakery import baker

from accounts.tests.mixins import AccountOneMixin
from core.redis import redis_client_instance as cache
from core.tests import TestCase
from core.utils import get_full_file_path

from .. import models
from ..api import schemas


class StoreSchemaTestCase(AccountOneMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.tmp_image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        self.item = baker.make(
            models.Item,
            name='Test Item',
            foreground_image=self.tmp_image,
            background_image=self.tmp_image,
            price=9.90,
            is_available=True,
        )
        self.box = baker.make(
            models.Box,
            name='Test Box',
            foreground_image=self.tmp_image,
            background_image=self.tmp_image,
            price=9.90,
            is_available=True,
        )
        self.collection = baker.make(
            models.Collection,
            name='Test Collection',
            foreground_image=self.tmp_image,
            background_image=self.tmp_image,
            price=9.90,
            is_available=True,
        )
        self.box_item = baker.make(
            models.Item,
            box=self.box,
            name='Test Box Item',
            foreground_image=self.tmp_image,
            background_image=self.tmp_image,
            price=9.90,
            is_available=True,
        )
        self.collection_item = baker.make(
            models.Item,
            collection=self.collection,
            name='Test Collection Item',
            foreground_image=self.tmp_image,
            background_image=self.tmp_image,
            price=9.90,
            is_available=True,
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
            'price': Decimal(str(self.item.price)),
            'release_date': self.item.release_date,
            'description': self.item.description,
            'discount': self.item.discount,
            'background_image': get_full_file_path(self.item.background_image),
            'foreground_image': get_full_file_path(self.item.foreground_image),
            'box': schemas.BoxSchema.from_orm(self.item.box) if self.item.box else None,
            'box_draw_chance': self.item.box_draw_chance,
            'collection': schemas.CollectionSchema.from_orm(self.collection)
            if self.item.collection
            else None,
            'featured': self.item.featured,
            'in_use': None,
            'can_use': None,
        }
        self.assertEqual(payload, expected_payload)

    def test_item_box_schema(self):
        payload = schemas.ItemSchema.from_orm(self.box_item).dict()
        expected_payload = {
            'id': self.box_item.id,
            'name': self.box_item.name,
            'item_type': self.box_item.item_type,
            'subtype': self.box_item.subtype,
            'handle': self.box_item.handle,
            'price': Decimal(str(self.box_item.price)),
            'release_date': self.box_item.release_date,
            'description': self.box_item.description,
            'discount': self.box_item.discount,
            'background_image': get_full_file_path(self.box_item.background_image),
            'foreground_image': get_full_file_path(self.box_item.foreground_image),
            'box': schemas.BoxSchema.from_orm(self.box).dict(),
            'box_draw_chance': self.box_item.box_draw_chance,
            'collection': schemas.CollectionSchema.from_orm(self.collection).dict()
            if self.box_item.collection
            else None,
            'featured': self.box_item.featured,
            'in_use': None,
            'can_use': None,
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
            'price': Decimal(str(self.collection_item.price)),
            'release_date': self.collection_item.release_date,
            'description': self.collection_item.description,
            'discount': self.collection_item.discount,
            'background_image': get_full_file_path(
                self.collection_item.background_image
            ),
            'foreground_image': get_full_file_path(
                self.collection_item.foreground_image
            ),
            'box': schemas.BoxSchema.from_orm(self.collection_item.box).dict()
            if self.collection_item.box
            else None,
            'box_draw_chance': self.collection_item.box_draw_chance,
            'collection': schemas.CollectionSchema.from_orm(self.collection).dict(),
            'featured': self.collection_item.featured,
            'in_use': None,
            'can_use': None,
        }
        self.assertEqual(payload, expected_payload)

    def test_box_schema(self):
        payload = schemas.BoxSchema.from_orm(self.box).dict()
        expected_payload = {
            'id': self.box.id,
            'name': self.box.name,
            'handle': self.box.handle,
            'price': Decimal(str(self.box.price)),
            'release_date': self.box.release_date,
            'description': self.box.description,
            'discount': self.box.discount,
            'background_image': get_full_file_path(self.box.background_image),
            'foreground_image': get_full_file_path(self.box.foreground_image),
            'featured': self.box.featured,
            'can_open': None,
        }
        self.assertEqual(payload, expected_payload)

    def test_collection_schema(self):
        payload = schemas.CollectionSchema.from_orm(self.collection).dict()
        expected_payload = {
            'id': self.collection.id,
            'name': self.collection.name,
            'handle': self.collection.handle,
            'price': Decimal(str(self.collection.price)),
            'release_date': self.collection.release_date,
            'description': self.collection.description,
            'discount': self.collection.discount,
            'background_image': get_full_file_path(self.collection.background_image),
            'foreground_image': get_full_file_path(self.collection.foreground_image),
            'featured': self.collection.featured,
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

        user_owned_item = baker.make(models.UserItem, item=self.item, user=self.user)
        payload = schemas.UserInventorySchema.from_orm(self.user).dict()
        expected_payload = {
            'id': f'{self.user.email}{self.user.id}inventory',
            'user_id': self.user.id,
            'items': [
                dict(
                    schemas.ItemSchema.from_orm(user_item.item).dict(),
                    in_use=user_owned_item.in_use,
                    can_use=user_owned_item.can_use,
                )
                for user_item in models.UserItem.objects.filter(user=self.user)
            ],
            'boxes': [],
        }
        self.assertEqual(payload, expected_payload)

        user_owned_box = baker.make(models.UserBox, box=self.box, user=self.user)
        payload = schemas.UserInventorySchema.from_orm(self.user).dict()
        expected_payload = {
            'id': f'{self.user.email}{self.user.id}inventory',
            'user_id': self.user.id,
            'items': [
                dict(
                    schemas.ItemSchema.from_orm(user_item.item).dict(),
                    in_use=user_owned_item.in_use,
                    can_use=user_owned_item.can_use,
                )
                for user_item in models.UserItem.objects.filter(user=self.user)
            ],
            'boxes': [
                dict(
                    schemas.BoxSchema.from_orm(user_box.box).dict(),
                    can_open=user_owned_box.can_open,
                )
                for user_box in models.UserBox.objects.filter(user=self.user)
            ],
        }

        self.assertEqual(payload, expected_payload)

    def test_user_store_schema(self):
        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        self.assertEqual(len(payload.get('products')), 4)
        self.assertEqual(payload.get('id'), f'{self.user.email}{self.user.id}store')
        self.assertEqual(payload.get('user_id'), self.user.id)

        baker.make(models.UserItem, item=self.item, user=self.user)
        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        self.assertEqual(len(payload.get('products')), 4)

        self.assertEqual(len(payload.get('featured')), 0)
        self.item.featured = True
        self.item.save()
        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        self.assertEqual(len(payload.get('featured')), 1)

        baker.make(
            models.Item,
            name='Test Item 2',
            foreground_image=self.tmp_image,
            background_image=self.tmp_image,
            price=9.90,
            is_available=False,
            featured=True,
        )

        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        self.assertEqual(len(payload.get('products')), 4)
        self.assertEqual(len(payload.get('featured')), 1)

    @override_settings(STORE_LENGTH=2)
    def test_user_store_schema_length(self):
        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        self.assertEqual(len(payload.get('products')), 2)

        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        self.assertEqual(len(payload.get('products')), 2)

    @override_settings(STORE_LENGTH=1)
    def test_user_store_schema_rotation(self):
        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        product1 = payload.get('products')[0]
        self.assertEqual(len(payload.get('products')), 1)

        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        product2 = payload.get('products')[0]
        self.assertEqual(len(payload.get('products')), 1)
        self.assertEqual(product1.get('id'), product2.get('id'))

        cache.delete(f'__store:user:{self.user.id}:last_updated')
        cache.delete(f'__store:user:{self.user.id}:items')
        cache.delete(f'__store:user:{self.user.id}:boxes')

        payload = schemas.UserStoreSchema.from_orm(self.user).dict()
        self.assertEqual(len(payload.get('products')), 1)
