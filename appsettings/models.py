from django.db import models


class AppSettings(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
