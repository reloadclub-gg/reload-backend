from typing import List

from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller, schemas

router = Router(tags=['notifications'])


@router.get(
    '/', auth=VerifiedRequiredAuth(), response={200: List[schemas.NotificationSchema]}
)
def list(request):
    return controller.list(user=request.user)


@router.patch(
    '/read-all/',
    auth=VerifiedRequiredAuth(),
    response={200: List[schemas.NotificationSchema]},
)
def read_all(request):
    return controller.read_all(user=request.user)


@router.get(
    '{notification_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.NotificationSchema},
)
def detail(request, notification_id: int):
    return controller.detail(user=request.user, notification_id=notification_id)


@router.patch(
    '{notification_id}/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.NotificationSchema},
)
def read(request, notification_id: int, payload: schemas.NotificationUpdateSchema):
    return controller.read(
        user=request.user, notification_id=notification_id, form=payload
    )
