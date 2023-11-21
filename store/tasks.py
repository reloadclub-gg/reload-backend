from datetime import datetime

from celery import shared_task

from .utils import send_purchase_mail


@shared_task
def send_purchase_mail_task(
    mail_to: str,
    transaction_id: int,
    transaction_date: datetime,
):
    send_purchase_mail(mail_to, transaction_id, transaction_date)
