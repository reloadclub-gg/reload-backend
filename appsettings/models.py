from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import signals
from django.dispatch import receiver
from django.utils.translation import gettext as _

from core.websocket import ws_create_toast, ws_maintenance
from lobbies.models import Lobby

User = get_user_model()


class AppSettings(models.Model):
    TEXT = 'text'
    INTEGER = 'integer'
    BOOLEAN = 'boolean'

    KIND_CHOICES = (
        (TEXT, _('Text')),
        (INTEGER, _('Integer')),
        (BOOLEAN, _('Boolean')),
    )

    kind = models.CharField(choices=KIND_CHOICES, default='text')
    name = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'
        indexes = [models.Index(fields=['name'])]

    @staticmethod
    def get(name, default=None):
        config = AppSettings.objects.filter(name=name)
        if config:
            config = config[0]
            if config.kind == AppSettings.TEXT:
                return str(config.value)
            elif config.kind == AppSettings.INTEGER:
                return int(config.value)
            elif config.kind == AppSettings.BOOLEAN:
                return bool(int(config.value))
            else:
                raise Exception('Unknown kind')

        return default

    def __str__(self):
        return self.name


@receiver(signals.post_save, sender=AppSettings)
def update_maintanence(sender, instance: AppSettings, created: bool, **kwargs):
    if instance.name == 'Maintenance Window' and not created:
        if AppSettings.get(instance.name) is True:
            Lobby.cancel_all_queues()
            ws_maintenance('start')
            ws_create_toast(
                _(
                    'We\'re about to start a maintenance. '
                    'All queues and invites will be disabled.'
                ),
                variant='warning',
            )

        else:
            ws_maintenance('end')
            ws_create_toast(
                _(
                    'The maintenance is over. '
                    'Queues and invites were enabled again. GLHF!'
                ),
                variant='success',
            )
