from django.conf import settings
from django.http import HttpResponse


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health-check':
            return HttpResponse('ok')
        return self.get_response(request)


class PortMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META['HTTP_HOST'] = settings.HOST_URL + settings.SITE_URL_SUFFIX
        response = self.get_response(request)
        return response
