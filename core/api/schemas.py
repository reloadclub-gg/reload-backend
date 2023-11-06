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


class HealthCheckSchema(Schema):
    language: str
    i18n_check: str
    maintenance: bool
    beta_required: bool
    invite_required: bool
