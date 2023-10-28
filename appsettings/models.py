from __future__ import annotations

from django.db import models
from django.utils.translation import gettext as _


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
