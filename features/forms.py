from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from . import models


class FeatureCreationForm(forms.ModelForm):
    ALL_ACTIVE_USERS = 0
    ONLINE_USERS = 1
    FILTER = (
        (ALL_ACTIVE_USERS, _("All active users")),
        (ONLINE_USERS, _("Online users")),
    )

    user_filter = forms.ChoiceField(
        widget=forms.RadioSelect(
            attrs={
                "onchange": """
                    window.location.href = event.target.value == 1
                    ? '?online=1'
                    : window.location.href.replace('?online=1', '')
                """,
                "class": "form-check-inline",
            },
        ),
        choices=FILTER,
    )

    class Media:
        js = ("admin/js/radio_custom_initial.js",)

    class Meta:
        model = models.Feature
        fields = "__all__"
        widgets = {
            "selected_users": forms.SelectMultiple(attrs={"class": "searchable"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        allowed_to = cleaned_data.get("allowed_to")
        selected_users = cleaned_data.get("selected_users")

        if allowed_to == models.Feature.AllowedChoices.SELECTED and not selected_users:
            raise ValidationError(
                {
                    "selected_users": _(
                        'At least one selected user is required for "selected" option.'
                    )
                }
            )

        elif allowed_to != models.Feature.AllowedChoices.SELECTED:
            cleaned_data["selected_users"] = []

        return cleaned_data
