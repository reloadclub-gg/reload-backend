from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller, schemas

router = Router(tags=["ranking"])


@router.get('/', auth=VerifiedRequiredAuth(), response={200: schemas.RankingSchema})
def list_ranking(request):
    return controller.ranking_list(request.user)
