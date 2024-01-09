from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from . import websocket
from .models import UserBan

User = get_user_model()


@receiver(post_save, sender=UserBan)
def inactivate_upon_ban(sender, instance: UserBan, created: bool, **kwargs):
    if created:
        instance.user.is_active = False
        instance.user.date_inactivation = timezone.now()
        instance.user.reason_inactivated = User.InactivationReason.USER_BAN

    elif instance.is_revoked:
        instance.user.is_active = True
        instance.user.date_inactivation = None
        instance.user.reason_inactivated = None

    instance.user.save()
    websocket.ws_update_user(instance.user)
    websocket.ws_update_status_on_friendlist(instance.user)
