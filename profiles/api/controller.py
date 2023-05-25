from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from ninja.errors import Http404
from social_django.models import UserSocialAuth

User = get_user_model()


def detail(user_id: int = None, steamid: int = None):
    user = None

    if user_id:
        user = get_object_or_404(User, pk=user_id, is_active=True)
    elif steamid:
        user = get_object_or_404(
            UserSocialAuth, extra_data__player__steamid=steamid
        ).user

    if hasattr(user, 'account') and user.account.is_verified:
        return user.account

    raise Http404()
