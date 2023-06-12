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
    public_profile: bool = True, username: bool = None
) -> dict:
    """
    Generate fake Steam data.
    """
    steamid = generate_random_string(length=18, allowed_chars='digits')
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
    user, public_profile: bool = True, username: bool = None
) -> UserSocialAuth:
    """
    Add a fake UserSocialAuth entry using the `generate_steam_extra_data` method
    to generate fake Steam data.

    :params user User: User model.
    """
    return baker.make(
        UserSocialAuth,
        user=user,
        extra_data=generate_steam_extra_data(
            public_profile=public_profile, username=username
        ),
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
