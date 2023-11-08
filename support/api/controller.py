from smtplib import SMTPException
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.translation import gettext as _
from ninja.errors import HttpError
from ninja.files import UploadedFile
from pydantic import BaseModel

from .schemas import REPORT_SUBJECT, TicketCreateSchema

User = get_user_model()


class Ticket(BaseModel):
    subject: str
    description: str
    attachments_count: int = 0


def create_ticket(
    user: User,
    payload: TicketCreateSchema,
    files: List[UploadedFile] = [],
) -> Ticket:
    ticket_info = f"""
    INFOS DO TICKET
    Assunto: {payload.subject}
    Conteúdo: {payload.description}
    """

    user_info = f"""
    INFOS DO USUÁRIO
    Email: {user.email}
    Steam ID: {user.steam_user.steamid}
    Admin URL: {settings.SITE_URL + reverse("admin:accounts_user_change", args=[user.id])}
    """

    body = ticket_info + user_info

    if payload.subject == REPORT_SUBJECT:
        reported_user = User.objects.get(pk=payload.report_user_id)
        reports_count = reported_user.reports_received.all().count()
        body += f"""
    INFOS DO DENUNCIADO
    Usuário denunciado: {reported_user.email}
    Quantidade de denúncias computadas: {reports_count}
    Steam ID: {reported_user.steam_user.steamid}
    Admin URL: {settings.SITE_URL + reverse("admin:accounts_user_change", args=[reported_user.id])}
        """

    email = EmailMessage(
        payload.subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.SUPPORT_EMAIL],
        headers={'Reply-To': user.email},
    )

    if files:
        for file in files:
            if file.size > 10000000:
                raise HttpError(400, _('Attachment is too large (max 10MB).'))

            with default_storage.open(f'uploads/{file.name}', 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            with default_storage.open(f'uploads/{file.name}', 'rb') as destination:
                email.attach(file.name, destination.read(), 'application/octet-stream')

    try:
        email.send()
    except SMTPException as e:
        raise HttpError(400, e)

    if files and not settings.TEST_MODE:
        for file in files:
            default_storage.delete(f'uploads/{file.name}')

    return Ticket(
        subject=payload.subject,
        description=payload.description,
        attachments_count=len(files),
    )
