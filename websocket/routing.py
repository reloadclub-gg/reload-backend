from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/', consumers.JsonAuthWebsocketConsumer.as_asgi(), name='ws_app'),
]
