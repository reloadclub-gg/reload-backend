import random
from datetime import timedelta
from typing import List, Optional, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Subquery
from django.utils import timezone
from ninja import Field, ModelSchema, Schema

from core.redis import redis_client_instance as cache
from core.utils import get_full_file_path, str_to_timezone

from .. import models

User = get_user_model()


class BoxSchema(ModelSchema):
    background_image: str
    foreground_image: str
    can_open: bool = None

    class Config:
        model = models.Box
        model_exclude = ['create_date', 'is_available', 'owners']

    @staticmethod
    def resolve_background_image(obj):
        return get_full_file_path(obj.background_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)


class CollectionSchema(ModelSchema):
    background_image: str
    foreground_image: str

    class Config:
        model = models.Collection
        model_exclude = ['create_date', 'is_available']

    @staticmethod
    def resolve_background_image(obj):
        return get_full_file_path(obj.background_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)


class ItemSchema(ModelSchema):
    background_image: str
    foreground_image: str
    box: BoxSchema = None
    collection: CollectionSchema = None
    in_use: bool = None
    can_use: bool = None

    class Config:
        model = models.Item
        model_exclude = ['create_date', 'is_available', 'owners']

    @staticmethod
    def resolve_background_image(obj):
        return get_full_file_path(obj.background_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)


class UserInventorySchema(ModelSchema):
    id: str
    user_id: int
    items: Optional[List[ItemSchema]] = []
    boxes: Optional[List[BoxSchema]] = []

    class Config:
        model = User
        model_fields = ['id']

    @staticmethod
    def resolve_items(obj):
        user_items = models.UserItem.objects.filter(
            user=obj,
            can_use=True,
        ).select_related('item')

        items = []
        for user_item in user_items:
            item = user_item.item
            item.in_use = user_item.in_use
            item.can_use = user_item.can_use
            item.id = user_item.id
            items.append(item)

        return items

    @staticmethod
    def resolve_boxes(obj):
        user_boxes = models.UserBox.objects.filter(
            user=obj,
            can_open=True,
        ).select_related('box')

        boxes = []
        for user_box in user_boxes:
            box = user_box.box
            box.can_open = user_box.can_open
            box.id = user_box.id
            boxes.append(box)

        return boxes

    @staticmethod
    def resolve_id(obj):
        return f'{obj.email}{obj.id}inventory'

    @staticmethod
    def resolve_user_id(obj):
        return obj.id


class UserStoreSchema(ModelSchema):
    id: str
    user_id: int
    featured: List[Union[ItemSchema, CollectionSchema, BoxSchema]] = []
    products: List[Union[ItemSchema, BoxSchema]] = []

    class Config:
        model = User
        model_fields = ['id']

    @staticmethod
    def get_featured_objects(model, **filters):
        return list(model.objects.filter(featured=True, is_available=True, **filters))

    @staticmethod
    def get_random_products(user: User):
        items = list(
            models.Item.objects.filter(is_available=True)
            .exclude(
                id__in=Subquery(
                    getattr(models, 'UserItem')
                    .objects.filter(user=user)
                    .values('item__id')
                )
            )
            .order_by('?')
        )

        boxes = list(
            models.Box.objects.filter(is_available=True)
            .exclude(
                id__in=Subquery(
                    getattr(models, 'UserBox')
                    .objects.filter(user=user)
                    .values('box__id')
                )
            )
            .order_by('?')
        )

        return items, boxes

    @staticmethod
    def resolve_featured(obj):
        return [
            item
            for sublist in [
                UserStoreSchema.get_featured_objects(models.Collection),
                UserStoreSchema.get_featured_objects(models.Item),
                UserStoreSchema.get_featured_objects(models.Box),
            ]
            for item in sublist
        ][: settings.STORE_FEATURED_MAX_LENGTH]

    @staticmethod
    def update_cache(key, values):
        if values:
            cache.sadd(key, *[item.id for item in values])

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

        reduced_items = [
            item for item in reduced_products if isinstance(item, models.Item)
        ]
        reduced_boxes = [box for box in reduced_products if isinstance(box, models.Box)]

        UserStoreSchema.update_cache(f'__store:user:{obj.id}:items', reduced_items)
        UserStoreSchema.update_cache(f'__store:user:{obj.id}:boxes', reduced_boxes)

        cache.set(rotation_key, timezone.now().isoformat())
        return reduced_products if reduced_products else []

    @staticmethod
    def get_cached_products(obj):
        items_ids = cache.smembers(f'__store:user:{obj.id}:items')
        boxes_ids = cache.smembers(f'__store:user:{obj.id}:boxes')
        items = models.Item.objects.filter(is_available=True, id__in=items_ids)
        boxes = models.Box.objects.filter(is_available=True, id__in=boxes_ids)
        products = list(items) + list(boxes)
        return products[: settings.STORE_LENGTH]

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
    price: str = Field(alias='default_price')
    amount: str

    @staticmethod
    def resolve_amount(obj):
        return obj.get('metadata').get('amount')


class PurchaseSchema(Schema):
    product_id: str
