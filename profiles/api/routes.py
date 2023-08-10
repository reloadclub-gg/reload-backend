from django.contrib.auth import get_user_model
from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller
from .schemas import ProfileSchema, ProfileUpdateSchema

User = get_user_model()

router = Router(tags=['profiles'])


@router.get('/', auth=VerifiedRequiredAuth(), response={200: ProfileSchema})
def detail(request, user_id: int = None, steamid: str = None, username: str = None):
    return controller.detail(user_id, steamid, username)


@router.patch('/', auth=VerifiedRequiredAuth(), response={200: ProfileSchema})
def update(request, payload: ProfileUpdateSchema):
    return controller.update(request.user, payload)
