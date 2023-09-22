import random
from datetime import timedelta
from typing import List, Optional, Union

from django.contrib.auth import get_user_model
from django.utils import timezone
from ninja import ModelSchema
from pydantic import Field

from core.redis import RedisClient
from core.utils import str_to_timezone

from .. import models

User = get_user_model()
cache = RedisClient()


class ItemSchema(ModelSchema):
    class Config:
        model = models.Item
        model_exclude = ['create_date', 'is_available']


class BoxSchema(ModelSchema):
    class Config:
        model = models.Box
        model_exclude = ['create_date', 'is_available']


class CollectionSchema(ModelSchema):
    class Config:
        model = models.Collection
        model_exclude = ['create_date', 'is_available']


class UserInventorySchema(ModelSchema):
    user_id: int = Field(None, alias='id')
    items: Optional[List[ItemSchema]] = []
    boxes: Optional[List[BoxSchema]] = []

    class Config:
        model = User
        model_fields = ['id']

    @staticmethod
    def resolve_items(obj):
        return models.UserItem.objects.filter(user=obj, item__can_use=True)

    @staticmethod
    def resolve_boxes(obj):
        return models.UserBox.objects.filter(user=obj, box__can_open=True)


class UserStoreSchema(ModelSchema):
    user_id: int = Field(None, alias='id')
    featured: List[Union[ItemSchema, CollectionSchema, BoxSchema]] = []
    products: List[Union[ItemSchema, BoxSchema]] = []

    class Config:
        model = User
        model_fields = ['id']

    @staticmethod
    def resolve_featured(obj):
        featured_items = list(
            models.Item.objects.filter(
                featured=True,
                is_available=True,
            )
        )
        featured_collections = list(
            models.Collection.objects.filter(
                featured=True,
                is_available=True,
            )
        )
        featured_boxes = list(
            models.Box.objects.filter(
                featured=True,
                is_available=True,
            )
        )

        return [
            item
            for sublist in [featured_collections, featured_items, featured_boxes]
            for item in sublist
        ]

    @staticmethod
    def resolve_products(obj):
        rotation = cache.get(f'__store:user:{obj.id}:last_updated')
        if rotation and timezone.now() - str_to_timezone(rotation) >= timedelta(days=1):
            products_ids = cache.smembers(f'__store:user:{obj.id}:products')
            return list(
                models.Item.objects.filter(
                    is_available=True,
                    id__in=products_ids,
                )
            )

        items = list(models.Item.objects.filter(is_available=True).order_by('?')[:12])
        boxes = list(models.Box.objects.filter(is_available=True).order_by('?')[:12])

        combined = items + boxes
        random.shuffle(combined)

        cache.sadd(
            f'__store:user:{obj.id}:products',
            [[item.id for item in combined[:12]]],
        )
        cache.set(f'__store:user:{obj.id}:last_updated', timezone.now().timestamp())
        return combined[:12]
