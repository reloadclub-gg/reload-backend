from ninja import Router
from accounts.api.auth import AuthBearer
from ..models import Lobby

router = Router(tags=['mm'])


@router.patch('lobby/leave/', auth=AuthBearer())
def lobby_leave(request):
    return Lobby.move(request.user.id)
