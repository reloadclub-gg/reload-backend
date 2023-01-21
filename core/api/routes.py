from django.conf import settings
from django.utils.translation import gettext as _
from ninja import NinjaAPI

from accounts.api.routes import router as accounts_router
from matchmaking.api.routes import router as mm_router

local_env = settings.ENVIRONMENT == settings.LOCAL
api = NinjaAPI(openapi_url=local_env and '/openapi.json' or '')
api.add_router("/accounts/", accounts_router)
api.add_router("/mm/", mm_router)


@api.get('')
def healty_check(request):
    lang = request.LANGUAGE_CODE
    return {'language': lang, 'i18n_check': _('Internationalization works.')}
