from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Feature

User = get_user_model()


def is_feat_available_for_user(feat_name: str, user: User) -> bool:

    if settings.TEST_MODE:
        return True

    try:
        feature = Feature.objects.get(name=feat_name)
    except Feature.DoesNotExist:
        return False

    check_conditions = {
        Feature.AllowedChoices.ALL: lambda u: True,
        Feature.AllowedChoices.ACTIVE: lambda u: u.is_active,
        Feature.AllowedChoices.ALPHA: lambda u: u.is_alpha,
        Feature.AllowedChoices.BETA: lambda u: u.is_beta,
        Feature.AllowedChoices.EARLY: lambda u: u.is_early,
        Feature.AllowedChoices.ONLINE: lambda u: u.is_online,
        Feature.AllowedChoices.VERIFIED: lambda u: u.account.is_verified,
        Feature.AllowedChoices.SELECTED: lambda u: u in feature.selected_users.all(),
    }

    return check_conditions.get(feature.allowed_to, lambda u: False)(user)
