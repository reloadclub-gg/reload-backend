import os

import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter

from websocket import routing

application = ProtocolTypeRouter(
    {
        'http': get_asgi_application(),
        'websocket': URLRouter(routing.websocket_urlpatterns),
    }
)
