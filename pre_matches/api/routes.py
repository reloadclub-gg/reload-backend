from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller, schemas

router = Router(tags=['pre-matches'])


@router.post(
    '/lock-in/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.PreMatchSchema},
)
def lock_in(request):
    return controller.set_player_lock_in(request.user)


@router.post(
    '/ready/',
    auth=VerifiedRequiredAuth(),
    response={200: schemas.PreMatchSchema},
)
def ready(request):
    return controller.set_player_ready(request.user)


@router.get('/', auth=VerifiedRequiredAuth(), response={200: schemas.PreMatchSchema})
def detail(request):
    return controller.get_pre_match(request.user)
