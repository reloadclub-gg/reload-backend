from typing import List

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from accounts.api.authentication import VerifiedRequiredAuth
from core.api.pagination import Pagination
from matches.models import Match

from . import controller
from .schemas import MatchSchema

router = Router(tags=['matches'])


@router.get('/{match_id}/', auth=VerifiedRequiredAuth(), response={200: MatchSchema})
def detail(request, match_id):
    return get_object_or_404(Match, id=match_id)


@router.get('/', auth=VerifiedRequiredAuth(), response={200: List[MatchSchema]})
@paginate(Pagination)
def list(request):
    return controller.get_user_matches(request.user)
