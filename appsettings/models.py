from django.db import models
from django.utils.translation import gettext as _


class AppSettings(models.Model):
    KIND_CHOICES = (
        ('text', _('Text')),
        ('integer', _('Integer')),
        ('boolean', _('Boolean')),
    )

    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    kind = models.CharField(choices=KIND_CHOICES, default='text')
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
