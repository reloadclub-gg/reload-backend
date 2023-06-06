from typing import List

from django.conf import settings
from django.utils.translation import gettext as _
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, Http404, ValidationError
from ninja.pagination import paginate

from accounts.api.routes import router as accounts_router
from friends.api.routes import router as friends_router
from lobbies.api.routes import router as lobbies_router
from matches.api.routes import router as matches_router
from matchmaking.api.routes import router as mm_router
from notifications.api.routes import router as notifications_router
from profiles.api.routes import router as profiles_router

from .pagination import Pagination

local_env = settings.ENVIRONMENT == settings.LOCAL
api = NinjaAPI(openapi_url=local_env and '/openapi.json' or '')


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


@api.get('/list/', response=List[dict])
@paginate(Pagination)
def list_items(request):
    if settings.ENVIRONMENT != settings.LOCAL:
        raise Http404()

    results = list()

    for i in range(0, 200):
        results.append({'id': i + 1})

    return results


api.add_router("/accounts/", accounts_router)
api.add_router("/mm/", mm_router)
api.add_router("/matches/", matches_router)
api.add_router("/notifications/", notifications_router)
api.add_router("/friends/", friends_router)
api.add_router("/profiles/", profiles_router)
api.add_router("/lobbies/", lobbies_router)
