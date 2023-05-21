from django.conf import settings
from django.utils.translation import gettext as _
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, ValidationError

from accounts.api.routes import router as accounts_router
from friends.api.routes import router as friends_router
from matches.api.routes import router as matches_router
from matchmaking.api.routes import router as mm_router
from notifications.api.routes import router as notifications_router

local_env = settings.ENVIRONMENT == settings.LOCAL
api = NinjaAPI(openapi_url=local_env and '/openapi.json' or '')
api.add_router("/accounts/", accounts_router)
api.add_router("/mm/", mm_router)
api.add_router("/matches/", matches_router)
api.add_router("/notifications/", notifications_router)
api.add_router("/friends/", friends_router)


@api.exception_handler(ValidationError)
def validation_errors(request, exc):
    errors = [
        {'loc': error['loc'], 'msg': _(error['msg']), 'type': error['type']}
        for error in exc.errors
    ]

    return api.create_response(request, {'detail': errors}, status=422)


@api.exception_handler(AuthenticationError)
def authentication_errors(request, exc):
    return api.create_response(request, {'detail': _('Unauthorized.')}, status=401)


@api.get('')
def healty_check(request):
    lang = request.LANGUAGE_CODE
    return {'language': lang, 'i18n_check': _('Internationalization works.')}
