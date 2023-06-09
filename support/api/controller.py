from smtplib import SMTPException
from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.utils.translation import gettext as _
from ninja.errors import HttpError
from ninja.files import UploadedFile
from pydantic import BaseModel

from .schemas import TicketCreateSchema

User = get_user_model()


class Ticket(BaseModel):
    subject: str
    description: str
    attachments_count: int = 0


def create_ticket(
    user: User,
    payload: TicketCreateSchema,
    files: List[UploadedFile] = None,
) -> Ticket:
    email = EmailMessage(
        payload.subject,
        body=payload.description,
        from_email=user.email,
        to=[settings.SUPPORT_EMAIL],
    )

    if files:
        for file in files:
            if file.size > 3000000:
                raise HttpError(400, _('Attachment is too large (max 3MB).'))

            with default_storage.open(f'tmp/{file.name}', 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
                    email.attach_file(destination.name)

    try:
        email.send()
    except SMTPException as e:
        raise HttpError(400, e)

    return Ticket(
        subject=payload.subject,
        description=payload.description,
        attachments_count=len(files) if files else 0,
    )
