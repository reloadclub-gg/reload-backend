import random
from datetime import datetime, timedelta
from typing import List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Subquery
from django.utils import timezone
from ninja import ModelSchema, Schema

from core.redis import redis_client_instance as cache
from core.utils import get_full_file_path, str_to_timezone

from .. import models

User = get_user_model()


class ItemMediaSchema(ModelSchema):
    class Config:
        model = models.ItemMedia
        model_exclude = ['item']

    @staticmethod
    def resolve_file(obj):
        return get_full_file_path(obj.file)


class ItemSchema(ModelSchema):
    background_image: str
    foreground_image: str
    box_id: int = None
    collection_id: int = None
    in_use: bool = None
    can_use: bool = None
    object: str = 'item'
    media: List[ItemMediaSchema] = []

    class Config:
        model = models.Item
        model_exclude = ['create_date', 'is_available', 'owners', 'box', 'collection']

    @staticmethod
    def resolve_background_image(obj):
        return get_full_file_path(obj.background_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)

    @staticmethod
    def resolve_media(obj):
        return obj.itemmedia_set.all()

    @staticmethod
    def resolve_box_id(obj):
        if obj.box:
            return obj.box.id

    @staticmethod
    def resolve_collection_id(obj):
        if obj.collection:
            return obj.collection.id


class BoxSchema(ModelSchema):
    background_image: str
    foreground_image: str
    can_open: bool = None
    object: str = 'box'
    items: List[ItemSchema] = []

    class Config:
        model = models.Box
        model_exclude = ['create_date', 'is_available', 'owners']

    @staticmethod
    def resolve_background_image(obj):
        return get_full_file_path(obj.background_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)

    @staticmethod
    def resolve_items(obj):
        return obj.item_set.filter(is_available=True)


class CollectionSchema(ModelSchema):
    background_image: str
    foreground_image: str
    object: str = 'collection'
    items: List[ItemSchema] = []

    class Config:
        model = models.Collection
        model_exclude = ['create_date', 'is_available']

    @staticmethod
    def resolve_background_image(obj):
        return get_full_file_path(obj.background_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)

    @staticmethod
    def resolve_items(obj):
        return obj.item_set.filter(is_available=True)


class UserItemSchema(ModelSchema):
    id: int
    name: str
    background_image: str
    foreground_image: str
    subtype: str = None
    description: str
    release_date: datetime = None
    item_type: str

    class Config:
        model = models.UserItem
        model_exclude = ['user', 'item']

    @staticmethod
    def resolve_name(obj):
        return obj.item.name

    @staticmethod
    def resolve_background_image(obj):
        return get_full_file_path(obj.item.background_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.item.foreground_image)

    @staticmethod
    def resolve_subtype(obj):
        return obj.item.subtype

    @staticmethod
    def resolve_description(obj):
        return obj.item.description

    @staticmethod
    def resolve_release_date(obj):
        return obj.item.release_date

    @staticmethod
    def resolve_item_type(obj):
        return obj.item.item_type


class UserBoxSchema(ModelSchema):
    id: int
    name: str
    background_image: str
    foreground_image: str
    description: str
    release_date: datetime = None

    class Config:
        model = models.UserBox
        model_exclude = ['user', 'box']

    @staticmethod
    def resolve_id(obj):
        return obj.box.id

    @staticmethod
    def resolve_name(obj):
        return obj.box.name

    @staticmethod
    def resolve_background_image(obj):
        return obj.box.background_image

    @staticmethod
    def resolve_foreground_image(obj):
        return obj.box.foreground_image

    @staticmethod
    def resolve_description(obj):
        return obj.box.description

    @staticmethod
    def resolve_release_date(obj):
        return obj.box.release_date


class UserInventorySchema(ModelSchema):
    id: str
    user_id: int
    items: Optional[List[UserItemSchema]] = []
    boxes: Optional[List[UserBoxSchema]] = []

    class Config:
        model = User
        model_fields = ['id']

    @staticmethod
    def resolve_items(obj):
        return models.UserItem.objects.filter(user=obj, can_use=True)

    @staticmethod
    def resolve_boxes(obj):
        return models.UserBox.objects.filter(user=obj, can_open=True)

    @staticmethod
    def resolve_id(obj):
        return f'{obj.email}{obj.id}inventory'

    @staticmethod
    def resolve_user_id(obj):
        return obj.id


class UserStoreSchema(ModelSchema):
    id: str
    user_id: int
    featured: list = []
    products: list = []
    next_rotation: str

    class Config:
        model = User
        model_fields = ['id']

    @staticmethod
    def get_featured_items(user):
        user_items = models.UserItem.objects.filter(user=user).values('item__id')
        return list(
            models.Item.objects.filter(featured=True, is_available=True).exclude(
                id__in=user_items
            )
        )

    @staticmethod
    def get_featured_boxes(user):
        user_boxes = models.UserBox.objects.filter(user=user).values('box__id')
        return list(
            models.Box.objects.filter(featured=True, is_available=True).exclude(
                id__in=user_boxes
            )
        )

    @staticmethod
    def get_featured_collections(user):
        user_item_ids = set(
            models.UserItem.objects.filter(user=user).values_list('item__id', flat=True)
        )
        collections = models.Collection.objects.filter(featured=True, is_available=True)

        result = []
        for collection in collections:
            collection_item_ids = set(collection.item_set.values_list('id', flat=True))
            if not collection_item_ids.intersection(user_item_ids):
                result.append(collection)

        return result

    @staticmethod
    def get_random_products(user: User):
        items = list(
            models.Item.objects.filter(is_available=True)
            .exclude(
                id__in=Subquery(
                    models.UserItem.objects.filter(user=user).values('item__id')
                )
            )
            .order_by('?')
        )

        boxes = list(
            models.Box.objects.filter(is_available=True)
            .exclude(
                id__in=Subquery(
                    models.UserBox.objects.filter(user=user).values('box__id')
                )
            )
            .order_by('?')
        )

        return items, boxes

    @staticmethod
    def resolve_featured(obj):
        model_to_schema = {
            models.Collection: CollectionSchema,
            models.Box: BoxSchema,
            models.Item: ItemSchema,
        }

        items = (
            UserStoreSchema.get_featured_collections(obj)
            + UserStoreSchema.get_featured_boxes(obj)
            + UserStoreSchema.get_featured_items(obj)
        )[: settings.STORE_FEATURED_MAX_LENGTH]

        return [model_to_schema[type(item)].from_orm(item) for item in items]

    @staticmethod
    def update_cache(key, values):
        if values:
            cache.sadd(key, *[item.id for item in values])

    @staticmethod
    def resolve_next_rotation(obj):
        rotation_key = f'__store:user:{obj.id}:last_updated'
        rotation = cache.get(rotation_key)
        now = timezone.now()
        duration = settings.STORE_ROTATION_DAYS

        if rotation:
            start_time = str_to_timezone(rotation)
            end_time = start_time + timedelta(days=duration)
        else:
            end_time = now + timedelta(days=duration)

        return end_time.isoformat()

    @staticmethod
    def resolve_products(obj):
        rotation_key = f'__store:user:{obj.id}:last_updated'
        rotation = cache.get(rotation_key)

        if rotation and timezone.now() - str_to_timezone(rotation) <= timedelta(
            days=settings.STORE_ROTATION_DAYS
        ):
            return UserStoreSchema.get_cached_products(obj)

        items, boxes = UserStoreSchema.get_random_products(obj)
        products = items + boxes
        random.shuffle(products)
        reduced_products = products[: settings.STORE_LENGTH]

        UserStoreSchema.update_cache(
            f'__store:user:{obj.id}:items',
            [item for item in reduced_products if isinstance(item, models.Item)],
        )
        UserStoreSchema.update_cache(
            f'__store:user:{obj.id}:boxes',
            [box for box in reduced_products if isinstance(box, models.Box)],
        )

        schemas = [
            ItemSchema.from_orm(item)
            if isinstance(item, models.Item)
            else BoxSchema.from_orm(item)
            for item in reduced_products
        ]

        cache.set(rotation_key, timezone.now().isoformat())
        return schemas if schemas else []

    @staticmethod
    def get_cached_products(obj):
        items_ids = cache.smembers(f'__store:user:{obj.id}:items')
        boxes_ids = cache.smembers(f'__store:user:{obj.id}:boxes')
        items = models.Item.objects.filter(is_available=True, id__in=items_ids).exclude(
            id__in=Subquery(models.UserItem.objects.filter(user=obj).values('item__id'))
        )
        boxes = models.Box.objects.filter(is_available=True, id__in=boxes_ids).exclude(
            id__in=Subquery(models.UserBox.objects.filter(user=obj).values('box__id'))
        )
        products = list(items) + list(boxes)
        reduced_products = products[: settings.STORE_LENGTH]
        return [
            ItemSchema.from_orm(item)
            if isinstance(item, models.Item)
            else BoxSchema.from_orm(item)
            for item in reduced_products
        ]

    @staticmethod
    def resolve_id(obj):
        return f'{obj.email}{obj.id}store'

    @staticmethod
    def resolve_user_id(obj):
        return obj.id


class UserItemUpdateSchema(Schema):
    in_use: bool


class ProductSchema(Schema):
    id: str
    name: str
    price: str
    amount: int


class PurchaseSchema(Schema):
    product_id: str
