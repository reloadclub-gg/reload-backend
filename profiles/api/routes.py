from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import Http404
from social_django.models import UserSocialAuth

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller
from .schemas import ProfileSchema

User = get_user_model()

router = Router(tags=['profiles'])


@router.get('/', response={200: ProfileSchema})
def detail(request, user_id: int = None, steamid: int = None):
    return controller.detail(user_id, steamid)
