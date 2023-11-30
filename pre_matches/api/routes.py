from typing import Union

from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth
from matches.api.schemas import MatchSchema
from matches.models import Match

from . import controller, schemas

router = Router(tags=['pre-matches'])


@router.post(
    '/ready/',
    auth=VerifiedRequiredAuth(),
    response={200: Union[schemas.PreMatchSchema, None], 201: MatchSchema},
)
def ready(request):
    result = controller.set_player_ready(request.user)
    if isinstance(result, Match):
        return 201, result

    return 200, result


@router.get('/', auth=VerifiedRequiredAuth(), response={200: schemas.PreMatchSchema})
def detail(request):
    return controller.get_pre_match(request.user)
