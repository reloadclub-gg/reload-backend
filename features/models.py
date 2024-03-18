from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Feature(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class FeaturePreview(models.Model):
    feature = models.OneToOneField(Feature, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, blank=True)

    class Meta:
        verbose_name = "Feature preview"
        verbose_name_plural = "Features preview"
