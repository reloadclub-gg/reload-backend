from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

channel_layer = get_channel_layer()


async def send_and_close(*args, **kwargs):
    """
    Helper method to send data and close connection right after data sent.
    This prevents websocket layers from hanging forever.
    """
    await channel_layer.send(*args, **kwargs)
    await channel_layer.close_pools()


async def ws_send(action, payload, groups=['global']):
    """
    Helper method that wraps `send_and_close` and
    prepare data to be sent over websockets.
    """
    meta = {'action': action, 'timestamp': str(timezone.now())}

    for group in groups:
        group_name = f'{settings.GROUP_NAME_PREFIX}.{group}'
        await send_and_close(
            group_name,
            {'type': 'send_payload', 'payload': payload, 'meta': meta},
        )
