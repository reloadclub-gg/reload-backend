from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Account

from .models import ProductTransaction


@receiver(post_save, sender=ProductTransaction)
def update_user_coins(sender, instance: ProductTransaction, created: bool, **kwargs):
    if created:
        Account.filter(user=instance.user).update(coins=instance.product.amount)
