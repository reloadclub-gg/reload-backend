from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import Account
from .utils import create_social_auth

User = get_user_model()


class UserAddForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'is_staff', 'is_superuser']

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.save()
        create_social_auth(user, username=user.email)
        Account.objects.create(user=user)


class UserUpdateForm(UserChangeForm):
    coins = forms.IntegerField(required=False, label='RC Wallet')
    level = forms.IntegerField(required=False)
    level_points = forms.IntegerField(required=False)

    class Meta(UserChangeForm.Meta):
        model = User

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'account'):
            self.fields['coins'].initial = self.instance.account.coins
            self.fields['level'].initial = self.instance.account.level
            self.fields['level_points'].initial = self.instance.account.level_points

    def save(self, commit=True):
        user = super().save(commit=commit)
        if self.instance and hasattr(self.instance, 'account'):
            self.instance.account.coins = self.cleaned_data['coins']
            self.instance.account.level = self.cleaned_data['level']
            self.instance.account.level_points = self.cleaned_data['level_points']
            if commit:
                self.instance.account.save()
                user.save()
            else:
                user._save_account = self.instance.account

        return user
