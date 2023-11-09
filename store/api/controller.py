import stripe
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ninja.errors import Http404, HttpError

from .. import models
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

    return user


def fetch_products():
    products = stripe.Product.list().get('data')
    return [schemas.ProductSchema.from_orm(product) for product in products]


def start_purchase(request, payload: schemas.PurchaseSchema):
    product = stripe.Product.retrieve(payload.product_id)
    if not product:
        raise Http404()

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'boleto'],
            line_items=[{'price': product.get('default_price'), 'quantity': 1}],
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
        )
        return {'client_secret': checkout_session.client_secret}
    except Exception as e:
        raise HttpError(400, str(e))
