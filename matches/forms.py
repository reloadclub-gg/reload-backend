from django import forms

from .models import Match


class MatchChatForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = 'chat'
