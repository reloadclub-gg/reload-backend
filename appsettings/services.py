from django.conf import settings

from .models import AppSettings


def check_invite_required():
    return AppSettings.get('Invite Required', settings.APP_INVITE_REQUIRED)


def matches_limit_per_server():
    return AppSettings.get('Matches Limit', settings.MATCHES_LIMIT_PER_SERVER)


def matches_limit_per_server_gap():
    return AppSettings.get('Matches Limit Gap', settings.MATCHES_LIMIT_PER_SERVER_GAP)
