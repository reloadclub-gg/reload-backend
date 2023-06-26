import pydantic
from django.utils.translation import gettext as _
from ninja import Schema


class ToastSchema(Schema):
    content: str
    variant: str = 'info'

    @pydantic.validator('variant')
    def variant_must_be_valid(cls, v):
        valid_values = ['info', 'warning', 'error', 'success']
        assert v in valid_values, _('Invalid toast variant.')
        return v
