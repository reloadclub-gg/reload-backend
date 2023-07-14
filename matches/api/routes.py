from typing import List

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import paginate

from accounts.api.authentication import VerifiedRequiredAuth
from core.api.pagination import Pagination
from matches.models import Match

from . import authorization, controller, schemas

router = Router(tags=['matches'])


@router.get(
    '/{match_id}/', auth=VerifiedRequiredAuth(), response={200: schemas.MatchSchema}
)
def detail(request, match_id: int):
    return get_object_or_404(Match, id=match_id)


@router.get('/', auth=VerifiedRequiredAuth(), response={200: List[schemas.MatchSchema]})
@paginate(Pagination)
def list(request, user_id: int = None):
    return controller.get_user_matches(request.user, user_id)


@authorization.whitelisted_required
@router.patch(
    '/{match_id}/',
    response={200: None},
)
def update(request, match_id: int, payload: schemas.MatchUpdateSchema):
    return controller.update_match(match_id, payload)
