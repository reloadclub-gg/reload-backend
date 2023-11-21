from datetime import datetime

from django.template.loader import render_to_string

from core.utils import send_mail


def send_purchase_mail(mail_to: str, transaction_id: int, transaction_date: datetime):
    """
    Send an e-mail to the user after a successful purchase.
    """
    html_content = render_to_string(
        'store/emails/success-email.html',
        {'transaction_id': transaction_id, 'transaction_date': transaction_date},
    )

    send_mail(
        [mail_to],
        'ReloadClub - Obrigado, sua compra foi concluída!',
        html_content,
    )
