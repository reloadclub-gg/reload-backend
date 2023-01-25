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
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'

    def __str__(self):
        return self.name
