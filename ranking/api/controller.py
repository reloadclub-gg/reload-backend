from django.conf import settings
from django.contrib.auth import get_user_model

from accounts.models import Account

User = get_user_model()


def ranking_list(user: User) -> dict:
    return Account.verified_objects.all().order_by('-level', '-level_points')[
        : settings.RANKING_LIMIT
    ]
