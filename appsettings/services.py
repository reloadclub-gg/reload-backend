from django.conf import settings

from .models import AppSettings


def check_invite_required() -> bool:
    return AppSettings.get('Invite Required', settings.APP_INVITE_REQUIRED)


def matches_limit_per_server() -> int:
    return AppSettings.get('Matches Limit', settings.MATCHES_LIMIT_PER_SERVER)


def matches_limit_per_server_gap() -> int:
    return AppSettings.get('Matches Limit Gap', settings.MATCHES_LIMIT_PER_SERVER_GAP)


def player_max_level() -> int:
    return AppSettings.get('Player Max Level', settings.PLAYER_MAX_LEVEL)


def player_max_level_points() -> int:
    return AppSettings.get('Player Max Level Points', settings.PLAYER_MAX_LEVEL_POINTS)


def player_max_losing_level_points() -> int:
    return AppSettings.get(
        'Player Max Losing Level Points', settings.PLAYER_MAX_LOSE_LEVEL_POINTS
    )


def max_notification_history_count_per_player() -> int:
    return AppSettings.get(
        'Max Notification Count Per Player',
        settings.MAX_NOTIFICATION_HISTORY_COUNT_PER_PLAYER,
    )


def maintenance_window() -> bool:
    return AppSettings.get('Maintenance Window', False)


def check_beta_required() -> bool:
    return AppSettings.get('Beta Required', False)


def check_alpha_required() -> bool:
    return AppSettings.get('Alpha Required', False)


def replaceable_store_items() -> bool:
    return AppSettings.get('Replaceable Store Items', False)


def is_restriction_on() -> bool:
    return AppSettings.get('Dodges Restriction', False)
