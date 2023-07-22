from django.contrib.auth import get_user_model

from ..models import Account

User = get_user_model()


def has_account(user: User) -> bool:
    """
    Return weather the received user has an account.
    """
    try:
        return user.account
    except Account.DoesNotExist as e:
        return False


def is_verified(user: User) -> bool:
    """
    Return weather the received user has an account and is verified.
    """
    return user.is_active and has_account(user) and user.account.is_verified
