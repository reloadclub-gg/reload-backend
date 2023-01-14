from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

channel_layer = get_channel_layer()


async def ws_send(action, payload, groups=['global']):
    """
    Helper method that send data over websockets.
    """
    meta = {'action': action, 'timestamp': str(timezone.now())}

    for group in groups:
        group_name = f'{settings.GROUP_NAME_PREFIX}.{group}'
        await channel_layer.group_send(
            group_name,
            {'type': 'send_payload', 'payload': payload, 'meta': meta},
        )
