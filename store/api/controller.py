import logging
from typing import List

import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from ninja.errors import Http404, HttpError

from lobbies.websocket import ws_update_lobby

from .. import models, tasks
from . import schemas

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


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

        if item.item.subtype == models.Item.SubType.CARD:
            ws_update_lobby(user.account.lobby)

    return user


def get_user_store(user: User) -> models.UserStore:
    if not hasattr(user, 'userstore'):
        models.UserStore.populate(user)

    return user.userstore


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
            for item in collection.item_set.all():
                user_item = user.useritem_set.create(item=item)
                user_items.append(user_item)
    except IntegrityError as e:
        logging.error(e)
        raise HttpError(400, _('Cannot process purchase.'))

    return user_items


def fetch_price(price_id: str):
    price = stripe.Price.retrieve(price_id).get('unit_amount_decimal')[:-2]
    decimals = stripe.Price.retrieve(price_id).get('unit_amount_decimal')[-2:]
    return f'R$ {price},{decimals}'


def fetch_products():
    products = stripe.Product.list(active=True).get('data')
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
                cancel_url=f'{settings.FRONT_END_URL}/checkout/cancel',
                metadata={'tid': checkout_transaction.id},
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

    payment_intent = stripe.PaymentIntent.retrieve(
        checkout_session.get('payment_intent')
    )
    user.account.coins += transaction.amount
    user.account.save()
    transaction.payment_method = payment_intent.get('payment_method_types')[0]
    transaction.complete_date = timezone.now()
    transaction.status = models.ProductTransaction.Status.COMPLETE
    transaction.succeeded = True
    transaction.save()
    tasks.send_purchase_mail_task.delay(
        user.email,
        transaction.id,
        transaction.complete_date,
    )
    return redirect(f'{settings.FRONT_END_URL}/checkout/success')


def _verify_checkout_session(request) -> stripe.Event:
    try:
        sig_header = request.headers.get('Stripe-Signature')
        return stripe.Webhook.construct_event(
            request.body,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        raise e
    except stripe.error.SignatureVerificationError as e:
        raise e


def _get_transaction(transaction_id: int) -> models.ProductTransaction:
    transaction = get_object_or_404(
        models.ProductTransaction,
        id=transaction_id,
        complete_date=None,
        status=models.ProductTransaction.Status.OPEN,
    )

    if not hasattr(transaction.user, 'account'):
        logging.warning(f'User {transaction.user.id} without account made a purchase.')

    return transaction


def _get_payment_method(payment_intent_id: str) -> str:
    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    return payment_intent.get('payment_method_types')[0]


def _complete_transaction(
    transaction: models.ProductTransaction,
    succeeded: bool = True,
):
    transaction.user.account.coins += transaction.amount
    transaction.user.account.save()
    transaction.succeeded = succeeded
    transaction.status = models.ProductTransaction.Status.COMPLETE
    transaction.complete_date = timezone.now()
    transaction.save()

    tasks.send_purchase_mail_task.delay(
        transaction.user.email,
        transaction.id,
        transaction.complete_date,
    )


def update_transactions(request):
    event = _verify_checkout_session(request)
    listening_types = [
        'checkout.session.async_payment_succeeded',
        'checkout.session.async_payment_failed',
        'checkout.session.completed',
    ]

    if event.get('type') in listening_types:
        transaction = _get_transaction(event['data']['object']['metadata']['tid'])
        checkout_session = stripe.checkout.Session.retrieve(transaction.session_id)
        payment_intent_id = checkout_session.get('payment_intent')
        transaction.payment_method = _get_payment_method(payment_intent_id)

        # if is an event to inform that the checkout session is done
        # we don't need to check the status of the entire transaction
        if event.get('type') == 'checkout.session.completed' or (
            event.get('type') != 'checkout.session.completed'
            and checkout_session.get('status')
            != models.ProductTransaction.Status.COMPLETE
        ):
            transaction.save()
            return

        succeeded = event.get('type') == 'checkout.session.async_payment_succeeded'
        _complete_transaction(transaction, succeeded)

    return {}
