from django.contrib.auth import get_user_model

from .models import Feature, FeaturePreview

User = get_user_model()


def is_feat_available_for_user(feat_name: str, user: User) -> bool:
    if Feature.objects.filter(name=feat_name).exists():
        try:
            FeaturePreview.objects.get(feature__name=feat_name, users=user)
        except FeaturePreview.DoesNotExist:
            return False

    return True
