from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

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
