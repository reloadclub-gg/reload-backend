from typing import List

from django.contrib.auth import get_user_model
from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller, schemas

User = get_user_model()

router = Router(tags=['store'])


@router.get(
    '/inventory/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.UserInventorySchema},
)
def inventory_list(request):
    return request.user


@router.patch(
    '/inventory/{item_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.UserInventorySchema},
)
def update(request, item_id: int, payload: schemas.UserItemUpdateSchema):
    return controller.item_update(request.user, item_id, payload)


@router.get('/', auth=VerifiedRequiredAuth(), response={200: schemas.UserStoreSchema})
def list(request):
    return request.user


@router.post(
    '/items/{item_id}/',
    auth=VerifiedRequiredAuth(),
    response={201: schemas.UserItemSchema},
)
def item_purchase(request, item_id: int):
    return controller.purchase_item(request.user, item_id)


@router.post(
    '/boxes/{box_id}/',
    auth=VerifiedRequiredAuth(),
    response={201: schemas.UserBoxSchema},
)
def box_purchase(request, box_id: int):
    return controller.purchase_box(request.user, box_id)


@router.post(
    '/collections/{collection_id}/',
    auth=VerifiedRequiredAuth(),
    response={201: List[schemas.ItemSchema]},
)
def collection_purchase(request, collection_id: int):
    return controller.purchase_collection(request.user, collection_id)


@router.get(
    '/products/',
    auth=VerifiedRequiredAuth(),
    response={200: List[schemas.ProductSchema]},
)
def rc_list(request):
    return controller.fetch_products()


@router.post(
    '/products/',
    auth=VerifiedRequiredAuth(),
    response={201: dict},
)
def rc_buy(request, payload: schemas.PurchaseSchema):
    return controller.buy_product(request, payload)
