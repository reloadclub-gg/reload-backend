from .models import AppSettings


def check_invite_required():
    return AppSettings.get('Invite Required')
