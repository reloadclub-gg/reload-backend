from django.contrib.auth import get_user_model
from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller
from .schemas import FriendListSchema

User = get_user_model()

router = Router(tags=['friends'])


@router.get('/', auth=VerifiedRequiredAuth(), response={200: FriendListSchema})
def friends_list(request):
    return controller.list(request.user)
