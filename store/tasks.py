from datetime import datetime

from celery import shared_task
from django.contrib.auth import get_user_model

from . import models
from .utils import send_purchase_mail

User = get_user_model()


@shared_task
def send_purchase_mail_task(
    mail_to: str,
    transaction_id: int,
    transaction_date: datetime,
):
    send_purchase_mail(mail_to, transaction_id, transaction_date)


@shared_task
def repopulate_user_store(user_id: int):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExsist:
        user = None

    if user:
        models.UserStore.populate(user)
