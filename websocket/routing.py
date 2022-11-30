from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('', consumers.JsonAuthWebsocketConsumer.as_asgi(), name='ws_auth'),
]
