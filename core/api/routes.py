from ninja import NinjaAPI

from django.conf import settings

from accounts.api.routes import router as accounts_router

local_env = settings.ENVIRONMENT == settings.LOCAL
api = NinjaAPI(openapi_url=local_env and '/openapi.json' or '')
api.add_router("/accounts/", accounts_router)


@api.get('')
def healty_check(request):
    return {'status': 'ok'}
