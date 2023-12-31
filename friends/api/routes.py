from django.contrib.auth import get_user_model
from ninja import Router

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller, schemas

User = get_user_model()

router = Router(tags=['friends'])


@router.post(
    '/{str:username}/',
    auth=VerifiedRequiredAuth(),
    response={201: schemas.FriendshipSchema},
)
def friends_add(request, username: str):
    return controller.add_friend(request.user, username)


# this isn't actual a username, this is a user_id, but Django URL resolver sucks:
# https://github.com/vitalik/django-ninja/issues/792
# That's why we need to convert to int, because it needs to be
# the same param with the same casting
@router.delete('/{str:username}/', auth=VerifiedRequiredAuth())
def friends_remove(request, username: str):
    return controller.remove_friend(request.user, int(username))


@router.get('/requests/', auth=VerifiedRequiredAuth(), response={200: dict})
def friends_requests(request):
    return controller.list_requests(request.user)


@router.post(
    '/requests/{friendship_id}/',
    auth=VerifiedRequiredAuth(),
    response={201: schemas.FriendSchema},
)
def friends_accept(request, friendship_id: int):
    return controller.accept_request(request.user, friendship_id)


@router.delete('/requests/{friendship_id}/', auth=VerifiedRequiredAuth())
def friends_refuse(request, friendship_id: int):
    return controller.refuse_request(request.user, friendship_id)


@router.get('/', auth=VerifiedRequiredAuth(), response={200: schemas.FriendListSchema})
def friends_list(request):
    return controller.list(request.user)
