from django.conf import settings

from .models import AppSettings


def check_invite_required():
    return AppSettings.get('Invite Required', settings.APP_INVITE_REQUIRED)


def matches_limit_per_server():
    return AppSettings.get('Matches Limit', settings.MATCHES_LIMIT_PER_SERVER)


def matches_limit_per_server_gap():
    return AppSettings.get('Matches Limit Gap', settings.MATCHES_LIMIT_PER_SERVER_GAP)


def player_max_level():
    return AppSettings.get('Player Max Level', settings.PLAYER_MAX_LEVEL)


def player_max_level_points():
    return AppSettings.get('Player Max Level Points', settings.PLAYER_MAX_LEVEL_POINTS)
