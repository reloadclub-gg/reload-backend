import secrets

from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from social_django.models import UserSocialAuth

from .models import Auth


class SteamAuthWebHook(View):
    """
    View that authenticate users via OpenID with Steam.
    """

    def get(self, request):
        if not request.user.is_active:
            return redirect(settings.FRONT_END_INACTIVE_URL)

        auth = Auth(user_id=request.user.pk)
        auth.create_token()
        request.user.last_login = timezone.now()

        # Search if user has more then 1 SocialAuth related, then delete others
        # so user can only have only one association
        UserSocialAuth.objects.filter(
            id__in=list(
                UserSocialAuth.objects.filter(user_id=request.user.pk).values_list(
                    'pk', flat=True
                )[1:]
            )
        ).delete()

        # If a user login and don't have an e-mail, UserSocialDjango is getting that user. I think
        # that is because email field is unique and None, so there should be some try/except in any
        # point of UserSocialDjango that checks for EMAIL_FIELD or USERNAME_FIELD and do some bad
        # strategy in case of a exception. So, we add a random email so UserSocialDjango don't
        # fuck with session scope.
        if not request.user.email:
            request.user.email = f'not_registered__{secrets.token_urlsafe(10)}@3c.gg'
            request.user.save()

        logout(request)
        return redirect(settings.FRONT_END_AUTH_URL.format(auth.token))
