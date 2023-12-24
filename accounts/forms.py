from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from social_django.models import UserSocialAuth

from .models import Account
from .tasks import send_verify_email
from .utils import create_social_auth

User = get_user_model()


class UserAddForm(UserCreationForm):
    steamid = forms.CharField(max_length=128, required=True)
    username = forms.CharField(max_length=64, required=True)

    class Meta:
        model = User
        fields = '__all__'

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.save()
        username = self.cleaned_data['username']
        steamid = self.cleaned_data['steamid']
        UserSocialAuth.objects.filter(steamid=steamid).delete()
        User.objects.filter(social_auth__uid=steamid, account__is_null=True).delete()
        create_social_auth(user, username=username, steamid=steamid)
        account = Account.objects.create(user=user, steamid=steamid, username=username)
        send_verify_email.delay(user.email, username, account.verification_token)
        return user

    def clean_username(self):
        return self.cleaned_data['username']

    def clean_steamid(self):
        return self.cleaned_data['steamid']


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
            self.fields['is_alpha'].label = 'Alpha'
            self.fields['is_beta'].label = 'Beta'

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
