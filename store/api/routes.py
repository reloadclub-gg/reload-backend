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