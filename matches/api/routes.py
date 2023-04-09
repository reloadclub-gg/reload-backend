from django.shortcuts import get_object_or_404
from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth
from matches import models

from .schemas import MatchSchema

router = Router(tags=['matches'])


@router.get('/{match_id}/', auth=VerifiedRequiredAuth(), response={200: MatchSchema})
def match_detail(request, match_id):
    return get_object_or_404(models.Match, id=match_id)
