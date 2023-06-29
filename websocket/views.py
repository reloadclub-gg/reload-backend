from django.shortcuts import render
from django.views.decorators.cache import never_cache

from accounts import websocket as accounts_websocket
from core import websocket as core_websocket
from friends import websocket as friends_websocket
from lobbies import websocket as lobbies_websocket
from matches import websocket as matches_websocket
from notifications import websocket as notifications_websocket
from pre_matches import websocket as pre_matches_websocket


def get_schema(name):
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


def generate_docs(ws, method):
    docstring = getattr(ws, method).__doc__
    if not docstring:
        return {}

    overview, cases, payload, actions = (
        docstring.replace('Cases:', '|')
        .replace('Payload:', '|')
        .replace('Actions:', '|')
        .split('|')
    )
    payload_split = payload.split(':')
    if len(payload_split) < 2:
        payload_repr = None
        payload_type = payload_split[0]
    else:
        payload_type = payload_split[1]
        repr_module = get_schema(' '.join(payload_split[0].split()))
        payload_repr = {
            'name': payload_split[0],
            'schema': dict(
                (key, value.get('type', value.get('$ref')).split('/')[-1])
                for key, value in repr_module.schema().get('properties').items()
            ),
        }

    return {
        'overview': overview,
        'cases': cases.split('- ')[1:],
        'payload': {'repr': payload_repr, 'type': payload_type},
        'actions': actions.split('- ')[1:],
    }


@never_cache
def docs(request):
    context = {
        'items': [
            {
                'title': 'accounts',
                'methods': [
                    {'name': method, 'doc': generate_docs(accounts_websocket, method)}
                    for method in dir(accounts_websocket)
                    if method.startswith('ws_') and method != 'ws_send'
                ],
            },
            {
                'title': 'core',
                'methods': [
                    {
                        'name': method,
                        'doc': generate_docs(core_websocket, method),
                    }
                    for method in dir(core_websocket)
                    if method.startswith('ws_') and method != 'ws_send'
                ],
            },
            {
                'title': 'friends',
                'methods': [
                    {'name': method, 'doc': generate_docs(friends_websocket, method)}
                    for method in dir(friends_websocket)
                    if method.startswith('ws_') and method != 'ws_send'
                ],
            },
            {
                'title': 'lobbies',
                'methods': [
                    {'name': method, 'doc': generate_docs(lobbies_websocket, method)}
                    for method in dir(lobbies_websocket)
                    if method.startswith('ws_') and method != 'ws_send'
                ],
            },
            {
                'title': 'matches',
                'methods': [
                    {
                        'name': method,
                        'doc': generate_docs(matches_websocket, method),
                    }
                    for method in dir(matches_websocket)
                    if method.startswith('ws_') and method != 'ws_send'
                ],
            },
            {
                'title': 'notifications',
                'methods': [
                    {
                        'name': method,
                        'doc': generate_docs(notifications_websocket, method),
                    }
                    for method in dir(notifications_websocket)
                    if method.startswith('ws_') and method != 'ws_send'
                ],
            },
            {
                'title': 'pre_matches',
                'methods': [
                    {
                        'name': method,
                        'doc': generate_docs(pre_matches_websocket, method),
                    }
                    for method in dir(pre_matches_websocket)
                    if method.startswith('ws_') and method != 'ws_send'
                ],
            },
        ]
    }

    return render(request, "websocket/docs.html", context)
