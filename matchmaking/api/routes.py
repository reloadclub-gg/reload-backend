from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller
from .schemas import PreMatchSchema

router = Router(tags=['mm'])


@router.patch(
    'match/{match_id}/player-lock-in/',
    auth=VerifiedRequiredAuth(),
    response={200: PreMatchSchema},
)
def match_player_lock_in(request, match_id: str):
    return controller.match_player_lock_in(user=request.user, pre_match_id=match_id)


@router.patch(
    'match/{match_id}/player-ready/',
    auth=VerifiedRequiredAuth(),
    response={200: PreMatchSchema},
)
def match_player_ready(request, match_id: str):
    return controller.match_player_ready(user=request.user, pre_match_id=match_id)
