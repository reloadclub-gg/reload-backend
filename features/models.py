from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Feature(models.Model):

    class AllowedChoices(models.TextChoices):
        ALPHA = "alpha"
        BETA = "beta"
        EARLY = "early"
        ACTIVE = "active"
        ONLINE = "online"
        VERIFIED = "verified"
        SELECTED = "selected"
        NONE = "none"
        ALL = "all"

    name = models.CharField(max_length=64)
    allowed_to = models.CharField(
        max_length=16,
        choices=AllowedChoices.choices,
        default=AllowedChoices.NONE,
        help_text=(
            'If "selected" option is selected, you must choose, at least, one user to allow '
            "this feat. If any other option is selected, "
            '"selected users" will be ignored and erased'
        ),
    )
    selected_users = models.ManyToManyField(User, blank=True, null=True, help_text="")

    def __str__(self):
        return self.name
