from typing import List

from ninja import Router
from ninja.pagination import paginate

from accounts.api.authentication import VerifiedRequiredAuth
from core.api.pagination import Pagination
from features.api.feat_auth import feat_available
from profiles.api.schemas import ProfileSchema

from . import controller

router = Router(tags=["ranking"])


@router.get("/", auth=VerifiedRequiredAuth(), response={200: List[ProfileSchema]})
@paginate(Pagination)
@feat_available(feat_name="ranking")
def list_ranking(request):
    return controller.ranking_list(request.user)
