from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from ninja import Schema
from pydantic import root_validator, validator

User = get_user_model()

VALID_SUBJECTS = [
    'Relatar um bug - algo não está funcionando corretamente',
    'Reportar um usuário',
    'Sugestão de funcionalidade',
    'Ajuda',
]

REPORT_SUBJECT = 'Reportar um usuário'


class TicketSchema(Schema):
    subject: str
    description: str
    attachments_count: int


class TicketCreateSchema(Schema):
    subject: str
    description: str
    report_user_id: int = None

    @validator('subject')
    def must_be_valid(cls, v):
        assert v in VALID_SUBJECTS, _('Invalid ticket subject.')
        return v

    @root_validator
    def reports_must_have_report_user_id(cls, values):
        if values.get('subject') == REPORT_SUBJECT:
            assert values.get('report_user_id'), _(
                '"report_user_id" field cannot be blank for this subject.'
            )
        return values
