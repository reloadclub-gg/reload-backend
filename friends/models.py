from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _

User = get_user_model()


class Friendship(models.Model):
    user_from = models.ForeignKey(
        User,
        related_name='sent_friend_requests',
        on_delete=models.CASCADE,
    )
    user_to = models.ForeignKey(
        User,
        related_name='received_friend_requests',
        on_delete=models.CASCADE,
    )
    create_date = models.DateTimeField(auto_now_add=True)
    accept_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user_from', 'user_to']

    def validate_accounts(self):
        return (
            hasattr(self.user_from, 'account')
            and hasattr(self.user_to, 'account')
            and self.user_from.account.is_verified
            and self.user_to.account.is_verified
        )

    def clean(self):
        if self.user_from == self.user_to:
            raise ValidationError(_('Users cannot be friends with themselves.'))

        if Friendship.objects.filter(
            user_from=self.user_to,
            user_to=self.user_from,
        ).exists():
            raise ValidationError(_('Friendship already exists.'))

        if not self.validate_accounts():
            raise ValidationError(_('Users must have verified accounts.'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user_from.account.username} and {self.user_to.account.username} friendship'
