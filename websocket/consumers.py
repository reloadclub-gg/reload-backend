from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from django.conf import settings

from . import auth


class JsonAuthWebsocketConsumer(AsyncJsonWebsocketConsumer):
    """
    Base application consumer for all websockets connections.
    """
    async def connect(self):
        """
        Event called when the ws connection is open.
        It tries to authenticate the user and closes the connect if can't.
        """

        self.user = await sync_to_async(auth.authenticate)(self.scope)
        print(self.user)
        if not self.user:
            return await self.close()

        self.group_name = f'{settings.GROUP_NAME_PREFIX}.{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def send_payload(self, event):
        await self.send_json({'meta': event.get('meta'), 'payload': event.get('payload')})

    async def disconnect(self, close_code):
        """
        Event called when the ws connection is closed.
        We decrement the user session on Redis, so each connection represents
        one session with a unique token in cache.

        :params scope dict: The websocket connection context.
        """
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        if self.user:
            await sync_to_async(auth.disconnect)(self.user)
