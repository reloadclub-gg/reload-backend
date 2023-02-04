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

    @staticmethod
    def get(name):
        config = AppSettings.objects.filter(name=name)
        if config:
            config = config[0]
            if config.kind == AppSettings.TEXT:
                return str(config.value)
            elif config.kind == AppSettings.INTEGER:
                return int(config.value)
            elif config.kind == AppSettings.BOOLEAN:
                return bool(config.value)
            else:
                raise Exception('Unknown kind')

        return None

    @staticmethod
    def set_text(name: str, value: str) -> AppSettings:
        try:
            return AppSettings.objects.create(
                kind=AppSettings.TEXT, name=name, value=str(value)
            )
        except Exception as exc:
            raise exc

    @staticmethod
    def set_bool(name: str, value: bool) -> AppSettings:
        if not value:
            value = ''

        try:
            return AppSettings.objects.create(
                kind=AppSettings.BOOLEAN, name=name, value=str(value)
            )
        except Exception as exc:
            raise exc

    @staticmethod
    def set_int(name: str, value: int) -> AppSettings:
        try:
            return AppSettings.objects.create(
                kind=AppSettings.INTEGER, name=name, value=str(value)
            )
        except Exception as exc:
            raise exc

    def save(self, *args, **kwargs):
        if self.kind == AppSettings.BOOLEAN:
            if not self.value:
                self.value = ''

        super(AppSettings, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
