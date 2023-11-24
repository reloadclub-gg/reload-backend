import logging
import random
from typing import List

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from ninja.errors import Http404, HttpError

from core.redis import redis_client_instance as cache

from .. import models, tasks
from . import schemas

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_random_product(user_id: int):
    item, box = None, None
    items_on_store = cache.smembers(f'__store:user:{user_id}:items')
    items_on_store_ids = [int(item_id) for item_id in items_on_store]
    user_item_ids = models.UserItem.objects.filter(user__id=user_id).values_list(
        'item__id',
        flat=True,
    )

    available_items = (
        models.Item.objects.filter(is_available=True)
        .exclude(id__in=user_item_ids)
        .exclude(id__in=items_on_store_ids)
    )
    items_count = available_items.aggregate(count=Count('id'))['count']
    if items_count > 0:
        random_index = random.randint(0, items_count - 1)
        item = available_items[random_index]

    boxes_on_store = cache.smembers(f'__store:user:{user_id}:boxes')
    boxes_on_store_ids = [int(item_id) for item_id in boxes_on_store]
    user_box_ids = models.UserBox.objects.filter(user__id=user_id).values_list(
        'box__id',
        flat=True,
    )

    available_boxes = (
        models.Box.objects.filter(is_available=True)
        .exclude(id__in=user_box_ids)
        .exclude(id__in=boxes_on_store_ids)
    )
    boxes_count = available_boxes.aggregate(count=Count('id'))['count']
    if boxes_count > 0:
        random_index = random.randint(0, boxes_count - 1)
        box = available_boxes[random_index]

    choices = [obj for obj in [box, item] if obj is not None]
    return random.choice(choices) if choices else None


def replace_purchased_item(user_id: int):
    new_product = get_random_product(user_id)
    if new_product:
        item_key_name = 'items' if isinstance(new_product, models.Item) else 'boxes'
        cache.sadd(f'__store:user:{user_id}:{item_key_name}', new_product.id)
    return new_product


def item_update(user: User, item_id: int, payload: schemas.UserItemUpdateSchema):
    in_use = not payload.in_use
    item = get_object_or_404(
        models.UserItem,
        pk=item_id,
        user=user,
        in_use=in_use,
        can_use=True,
    )

    if item:
        item.in_use = payload.in_use
        item.save()

    return user


def fetch_price(price_id: str):
    price = stripe.Price.retrieve(price_id).get('unit_amount_decimal')[:-2]
    decimals = stripe.Price.retrieve(price_id).get('unit_amount_decimal')[-2:]
    return f'R$ {price},{decimals}'


def fetch_products():
    products = stripe.Product.list().get('data')
    reduced_products = [
        {
            'id': product.get('id'),
            'name': product.get('name'),
            'price': fetch_price(product.get('default_price')),
            'amount': int(product.get('metadata').get('amount')),
        }
        for product in products
    ]
    return sorted(
        [schemas.ProductSchema.from_orm(product) for product in reduced_products],
        key=lambda x: x.amount,
    )


def buy_product(request, payload: schemas.PurchaseSchema):
    product = stripe.Product.retrieve(payload.product_id)
    if not product:
        raise Http404()

    try:
        with transaction.atomic():
            checkout_transaction = models.ProductTransaction.objects.create(
                user=request.user,
                product_id=product.get('id'),
                amount=product.get('metadata').get('amount'),
                price=fetch_price(product.get('default_price')),
            )
            success_url = f'/api/store/products/transactions/{checkout_transaction.id}/'
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'boleto'],
                line_items=[{'price': product.get('default_price'), 'quantity': 1}],
                mode='payment',
                success_url=request.build_absolute_uri(success_url),
                cancel_url=f'{settings.FRONT_END_URL}/jogar',
            )

            checkout_transaction.session_id = checkout_session.get('id')
            checkout_transaction.save()
            return checkout_session
    except (IntegrityError, Exception) as e:
        logging.error(e)
        raise HttpError(400, _('Cannot process purchase.'))


def resume_transaction(transaction_id: int):
    transaction = get_object_or_404(
        models.ProductTransaction,
        id=transaction_id,
        complete_date=None,
        status=models.ProductTransaction.Status.OPEN,
    )
    user = transaction.user
    checkout_session = stripe.checkout.Session.retrieve(transaction.session_id)

    if (
        not hasattr(user, 'account')
        or checkout_session.get('status') != models.ProductTransaction.Status.COMPLETE
    ):
        return redirect(f'{settings.FRONT_END_URL}/checkout/error')

    user.account.coins += transaction.amount
    user.account.save()
    transaction.complete_date = timezone.now()
    transaction.status = models.ProductTransaction.Status.COMPLETE
    transaction.save()
    tasks.send_purchase_mail_task.delay(
        user.email,
        transaction.id,
        transaction.complete_date,
    )
    return redirect(f'{settings.FRONT_END_URL}/checkout/success')


def purchase_item(user: User, item_id: int) -> models.UserItem:
    item = get_object_or_404(models.Item, id=item_id)

    if not item.is_available:
        raise HttpError(400, _('Item not available.'))

    if item.price > user.account.coins:
        raise HttpError(403, _('Insufficient funds.'))

    try:
        with transaction.atomic():
            user.account.coins -= item.price
            user.account.save()
            user_item = user.useritem_set.create(item=item)
    except IntegrityError as e:
        logging.error(e)
        raise HttpError(400, _('Cannot process purchase.'))

    cache.srem(f'__store:user:{user.id}:items', item.id)
    replace_purchased_item(user_id=user.id)
    return user_item


def purchase_box(user: User, box_id: int) -> models.UserBox:
    box = get_object_or_404(models.Box, id=box_id)

    if not box.is_available:
        raise HttpError(400, _('Item not available.'))

    if box.price > user.account.coins:
        raise HttpError(403, _('Insufficient funds.'))

    try:
        with transaction.atomic():
            user.account.coins -= box.price
            user.account.save()
            user_box = user.userbox_set.create(box=box)
    except IntegrityError as e:
        logging.error(e)
        raise HttpError(400, _('Cannot process purchase.'))

    cache.srem(f'__store:user:{user.id}:boxes', box.id)
    replace_purchased_item(user_id=user.id)
    return user_box


def purchase_collection(user: User, collection_id: int) -> List[models.UserItem]:
    collection = get_object_or_404(models.Collection, id=collection_id)

    if not collection.is_available:
        raise HttpError(400, _('Item not available.'))

    if collection.price > user.account.coins:
        raise HttpError(403, _('Insufficient funds.'))

    user_items = []
    try:
        with transaction.atomic():
            user.account.coins -= collection.price
            user.account.save()
            for item in collection.item_set.filter(is_available=True):
                user_item = user.useritem_set.create(item=item)
                user_items.append(user_item)
                cached_items = cache.smembers(f'__store:user:{user.id}:items')
                if str(item.id) in cached_items:
                    cache.srem(f'__store:user:{user.id}:items', item.id)
                    replace_purchased_item(user_id=user.id)
    except IntegrityError as e:
        logging.error(e)
        raise HttpError(400, _('Cannot process purchase.'))

    return user_items
