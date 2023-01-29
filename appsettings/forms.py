from django import forms
from django.utils.translation import gettext as _

from .models import AppSettings


class AppSettingsForm(forms.ModelForm):
    class Meta:
        model = AppSettings
        fields = '__all__'

    def clean(self):
        kind = self.cleaned_data.get('kind')
        value = self.cleaned_data.get('value')

        if kind == self.Meta.model.INTEGER and not value.isdigit():
            raise forms.ValidationError(_('value is not integer'))

        if kind == self.Meta.model.BOOLEAN and value not in ['0', '1']:
            raise forms.ValidationError(_('value is not boolean'))

        return self.cleaned_data
