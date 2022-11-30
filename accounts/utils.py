from model_bakery import baker
from social_django.models import UserSocialAuth

from django.conf import settings
from django.template.loader import render_to_string

from core.utils import generate_random_string, send_mail


def generate_steam_extra_data(public_profile=True, username=None):
    steamid = generate_random_string(length=18, allowed_chars='digits')
    personaname = username or generate_random_string(length=9, allowed_chars='letters')
    communityvisibilitystate = 3 if public_profile else 0

    return {
        'player': {
            'steamid': steamid,
            'personaname': personaname,
            'communityvisibilitystate': communityvisibilitystate
        }
    }


def create_social_auth(user, public_profile=True, username=None) -> UserSocialAuth:
    return baker.make(
        UserSocialAuth,
        user=user,
        extra_data=generate_steam_extra_data(public_profile=public_profile, username=username)
    )


def send_verify_account_mail(mail_to, username, token):
    html_content = render_to_string(
        'accounts/emails/verify-email.html',
        {
            'username': username,
            'token': token,
            'url': settings.FRONT_END_VERIFY_URL.format(token)
        }
    )

    send_mail([mail_to], 'GTA MM - Bem vindo!', html_content)
