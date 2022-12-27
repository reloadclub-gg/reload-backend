from .models import AppSettings


def check_invite_required():
    return AppSettings.objects.filter(name='Invite Required', value='1').exists()
