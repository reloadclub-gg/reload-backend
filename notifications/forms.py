from django import forms
from django.utils.translation import gettext_lazy as _

from . import models


class SystemNotificationCreationForm(forms.ModelForm):
    ALL_ACTIVE_USERS = 0
    ONLINE_USERS = 1
    FILTER = (
        (ALL_ACTIVE_USERS, _('All active users')),
        (ONLINE_USERS, _('Online users')),
    )

    user_filter = forms.ChoiceField(
        widget=forms.RadioSelect(
            attrs={
                'onchange': """
                    window.location.href = event.target.value == 1
                    ? '?online=1'
                    : window.location.href.replace('?online=1', '')
                """,
                'class': 'form-check-inline',
            },
        ),
        choices=FILTER,
    )

    class Media:
        js = ('admin/js/radio_custom_initial.js',)

    class Meta:
        model = models.SystemNotification
        fields = '__all__'
