from datetime import datetime
from typing import Any, List, Optional

from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema

from core.utils import get_full_file_path

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
    cover_image: str
    foreground_image: str
    featured_image: str = None
    decorative_image: str = None
    preview_image: str = None
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
    def resolve_cover_image(obj):
        return get_full_file_path(obj.cover_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)

    @staticmethod
    def resolve_featured_image(obj):
        if obj.featured_image:
            return get_full_file_path(obj.featured_image)

    @staticmethod
    def resolve_decorative_image(obj):
        if obj.decorative_image:
            return get_full_file_path(obj.decorative_image)

    @staticmethod
    def resolve_preview_image(obj):
        if obj.preview_image:
            return get_full_file_path(obj.preview_image)

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
    cover_image: str
    foreground_image: str
    featured_image: str = None
    can_open: bool = None
    object: str = 'box'
    items: List[ItemSchema] = []

    class Config:
        model = models.Box
        model_exclude = ['create_date', 'is_available', 'owners']

    @staticmethod
    def resolve_cover_image(obj):
        return get_full_file_path(obj.cover_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)

    @staticmethod
    def resolve_featured_image(obj):
        if obj.featured_image:
            return get_full_file_path(obj.featured_image)

    @staticmethod
    def resolve_items(obj):
        return obj.item_set.filter(is_available=True)


class CollectionSchema(ModelSchema):
    cover_image: str
    foreground_image: str
    featured_image: str = None
    object: str = 'collection'
    items: List[ItemSchema] = []

    class Config:
        model = models.Collection
        model_exclude = ['create_date', 'is_available']

    @staticmethod
    def resolve_cover_image(obj):
        return get_full_file_path(obj.cover_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.foreground_image)

    @staticmethod
    def resolve_featured_image(obj):
        if obj.featured_image:
            return get_full_file_path(obj.featured_image)

    @staticmethod
    def resolve_items(obj):
        return obj.item_set.all()


class UserItemSchema(ModelSchema):
    id: int
    name: str
    cover_image: str
    foreground_image: str
    featured_image: str = None
    decorative_image: str = None
    preview_image: str = None
    subtype: str = None
    description: str
    release_date: datetime = None
    item_type: str
    item_id: int
    weapon: str = None
    media: List[ItemMediaSchema] = []

    class Config:
        model = models.UserItem
        model_exclude = ['user', 'item']

    @staticmethod
    def resolve_name(obj):
        return obj.item.name

    @staticmethod
    def resolve_cover_image(obj):
        return get_full_file_path(obj.item.cover_image)

    @staticmethod
    def resolve_foreground_image(obj):
        return get_full_file_path(obj.item.foreground_image)

    @staticmethod
    def resolve_featured_image(obj):
        if obj.item.featured_image:
            return get_full_file_path(obj.item.featured_image)

    @staticmethod
    def resolve_decorative_image(obj):
        if obj.item.decorative_image:
            return get_full_file_path(obj.item.decorative_image)

    @staticmethod
    def resolve_preview_image(obj):
        if obj.item.preview_image:
            return get_full_file_path(obj.item.preview_image)

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

    @staticmethod
    def resolve_item_id(obj):
        return obj.item.id

    @staticmethod
    def resolve_weapon(obj):
        if obj.item.weapon:
            return obj.item.weapon

    @staticmethod
    def resolve_media(obj):
        return obj.item.itemmedia_set.all()


class UserBoxSchema(ModelSchema):
    id: int
    name: str
    cover_image: str
    foreground_image: str
    featured_image: str = None
    description: str
    release_date: datetime = None
    box_id: int

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
    def resolve_cover_image(obj):
        return obj.box.cover_image

    @staticmethod
    def resolve_foreground_image(obj):
        return obj.box.foreground_image

    @staticmethod
    def resolve_featured_image(obj):
        if obj.box.featured_image:
            return obj.box.featured_image

    @staticmethod
    def resolve_description(obj):
        return obj.box.description

    @staticmethod
    def resolve_release_date(obj):
        return obj.box.release_date

    @staticmethod
    def resolve_box_id(obj):
        return obj.box.id


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
    user_id: int
    featured: List[Any] = []
    products: List[ItemSchema] = []
    next_rotation: str
    last_rotation: str

    class Config:
        model = models.UserStore
        model_exclude = ['user', 'items_ids', 'last_rotation_items_ids']

    @staticmethod
    def resolve_user_id(obj):
        return obj.user.id

    @staticmethod
    def resolve_next_rotation(obj):
        return obj.next_rotation_date.isoformat()

    @staticmethod
    def resolve_last_rotation(obj):
        return obj.last_rotation_date.isoformat()

    @staticmethod
    def resolve_featured(obj):
        return [
            ItemSchema.from_orm(item)
            if isinstance(item, models.Item)
            else CollectionSchema.from_orm(item)
            for item in obj.featured
        ]

    @staticmethod
    def resolve_products(obj):
        return [ItemSchema.from_orm(item) for item in obj.products]


class UserItemUpdateSchema(Schema):
    in_use: bool


class ProductSchema(Schema):
    id: str
    name: str
    price: str
    amount: int


class PurchaseSchema(Schema):
    product_id: str
