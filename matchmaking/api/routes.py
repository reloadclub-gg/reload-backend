from ninja import Router
from .auth import AuthBearer

router = Router(tags=['lobby'])


@router.get('exit/', auth=AuthBearer())
def exit(request):
    user = request.user
    return user.account.lobby.move(user.id, user.id, remove=True)
