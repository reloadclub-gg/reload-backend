import secrets

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from social_core.utils import setting_name
from social_django.models import UserSocialAuth
from social_django.utils import psa
from social_django.views import _do_login

from accounts.social_actions import do_complete

from .models import Auth, User


class AdminLogin(LoginView):
    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        if self.request.user.is_authenticated:
            self.request.user.status = User.Statuses.ONLINE
            self.request.user.save()

        return HttpResponseRedirect(self.get_success_url())


class AdminLogout(LogoutView):
    def get(self, request, *args, **kwargs):
        if (
            self.request.user.is_authenticated
            and self.request.user.status != User.Statuses.OFFLINE
        ):
            self.request.user.status = User.Statuses.OFFLINE
            self.request.user.save()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.request.user.status = User.Statuses.OFFLINE
        self.request.user.save()
        return super().post(request, *args, **kwargs)


class SteamAuthWebHook(View):
    """
    View that authenticate users via OpenID with Steam.
    """

    @method_decorator(login_required)
    def get(self, request):
        auth = Auth(user_id=request.user.pk)
        auth.create_token()
        request.user.last_login = timezone.now()

        if not request.user.is_active:
            logout(request)
            return redirect(settings.FRONT_END_AUTH_URL.format(auth.token))

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
            request.user.email = (
                f'not_registered__{secrets.token_urlsafe(10)}@reloadclub.gg'
            )
            request.user.save()

        logout(request)
        return redirect(settings.FRONT_END_AUTH_URL.format(auth.token))


# This is required by the complete view
NAMESPACE = getattr(settings, setting_name("URL_NAMESPACE"), None) or "social"


@never_cache
@csrf_exempt
@psa(f"{NAMESPACE}:complete")
def complete(request, backend, *args, **kwargs):
    """
    This view overrides the social_django.views.complete by calling the custom
    accounts.social_actions.do_complete, which allows inactive users to login.
    """
    return do_complete(
        request.backend,
        _do_login,
        user=request.user,
        redirect_name=REDIRECT_FIELD_NAME,
        request=request,
        *args,
        **kwargs,
    )
