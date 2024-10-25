from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from model_bakery import baker
from social_django.models import UserSocialAuth

from appsettings.services import player_max_level, player_max_level_points
from core.utils import generate_random_string, send_mail


def generate_steam_extra_data(
    public_profile: bool = True,
    username: str = None,
    steamid: str = None,
) -> dict:
    """
    Generate fake Steam data.
    """
    steamid = steamid or generate_random_string(length=18, allowed_chars='digits')
    personaname = username or generate_random_string(length=9, allowed_chars='letters')
    communityvisibilitystate = 3 if public_profile else 0

    return {
        'player': {
            'steamid': steamid,
            'personaname': personaname,
            'communityvisibilitystate': communityvisibilitystate,
            'profileurl': f'https://steamcommunity.com/profiles/{steamid}',
        }
    }


def create_social_auth(
    user,
    public_profile: bool = True,
    username: str = None,
    steamid: str = None,
) -> UserSocialAuth:
    """
    Add a fake UserSocialAuth entry using the `generate_steam_extra_data` method
    to generate fake Steam data.

    :params user User: User model.
    """
    extra_data = generate_steam_extra_data(
        public_profile=public_profile,
        username=username,
        steamid=steamid,
    )
    return baker.make(
        UserSocialAuth,
        user=user,
        extra_data=extra_data,
        uid=steamid or extra_data.get('player').get('steamid'),
        provider='steam',
    )


def send_verify_account_mail(mail_to: str, username: str, token: str):
    """
    Send an e-mail to the user, so he can verify that his e-mailbox exists.
    """
    html_content = render_to_string(
        'accounts/emails/verify-email.html',
        {
            'username': username,
            'token': token,
            'url': settings.FRONT_END_AUTH_URL.format(token),
        },
    )

    send_mail([mail_to], 'ReloadClub - Falta pouco!', html_content)


def send_welcome_mail(mail_to: str):
    """
    Send an e-mail to the user after a successful account verification.
    """
    html_content = render_to_string(
        'accounts/emails/welcome-email.html',
    )

    send_mail([mail_to], 'ReloadClub - Boas-vindas!', html_content)


def send_inactivation_mail(mail_to: str):
    """
    Send an e-mail to the user uppon account inactivation.
    """
    html_content = render_to_string(
        'accounts/emails/inactivation-email.html',
    )

    send_mail([mail_to], 'ReloadClub - Nos vemos em breve!', html_content)


def calc_level_and_points(
    points_earned: int, level: int, level_points: int
) -> tuple(int):
    """
    Here we calculate the new level points of a user.
    This method returns a tuple with the new level and the new level points: (X, Y).
    """
    max_points = player_max_level_points()
    max_lvl = player_max_level()

    if points_earned > max_points or points_earned < (max_points * -1):
        raise ValidationError(_('Level points should never exceed max level points.'))

    if points_earned + level_points >= max_points:
        # Player get to next level upon max points reached
        if level == max_lvl:
            # If player is on max level, it should not get to next level,
            # thus it doesn't exist
            return (level, level_points + points_earned)
        else:
            # The remaning points should be increased on the next level
            return (
                level + 1,
                points_earned + level_points - settings.PLAYER_MAX_LEVEL_POINTS,
            )
    elif points_earned + level_points <= 0:
        # Player get to prev level upon min points reached - if applicable
        if level == 0:
            # If player is on min level (0), it should not get to prev level,
            # thus it doesn't exist
            return level, 0
        else:
            return (level - 1, max_points + points_earned + level_points)
    else:
        # If there isn't any change on levels, just in points,
        # we just incr the points
        return (level, level_points + points_earned)


def steamid64_to_hex(steamid64: str) -> str:
    steamid_hex = hex(int(steamid64))
    if steamid_hex.startswith('0x'):
        steamid_hex = steamid_hex[2:]
    return steamid_hex


def hex_to_steamid64(steamid_hex: str) -> str:
    if not steamid_hex.startswith('0x'):
        steamid_hex = f'0x{steamid_hex}'
    return str(int(steamid_hex, 0)).zfill(17)  # 17 is the size of steamid64


def send_invite_mail(mail_to: str, from_username: str):
    """
    Send an e-mail to a user that has been invited.
    """
    html_content = render_to_string(
        'accounts/emails/invite-email.html',
        {'username': from_username},
    )

    send_mail([mail_to], 'ReloadClub - Você foi convidado!', html_content)
