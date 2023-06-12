from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja import Schema
from pydantic import validator

User = get_user_model()

VALID_SUBJECTS = [
    'Relatar um bug - algo não está funcionando corretamente',
    'Reportar um usuário',
    'Sugestão de funcionalidade',
    'Ajuda',
]


class TicketSchema(Schema):
    subject: str
    description: str
    attachments_count: int


class TicketCreateSchema(Schema):
    subject: str
    description: str

    @validator('subject')
    def must_be_valid(cls, v):
        assert v in VALID_SUBJECTS, _('Invalid ticket subject.')
        return v
