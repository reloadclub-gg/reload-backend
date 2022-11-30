from ninja.errors import HttpError

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.utils import get_ip_address
from websocket.controller import friendlist_add
from ..models import Account, Invite, Auth, UserLogin
from .. import utils

User = get_user_model()


def login(request, token: str) -> Auth:
    """
    Checks if there is any existing user for the given auth token and
    creates/update an UserLogin for that user with the request IP address.
    """
    auth = Auth.load(token)
    if not auth:
        return

    user = User.objects.filter(pk=auth.user_id, is_active=True)
    if user.exists():
        user = user[0]
        UserLogin.objects.update_or_create(
            user=user,
            ip_address=get_ip_address(request),
            defaults={'timestamp': timezone.now()},
        )

        user.refresh_from_db()
        request.user = user
        return auth


def create_fake_user(email: str) -> User:
    user = User.objects.create(email=email)
    auth = Auth(user_id=user.pk)
    auth.create_token()
    user.last_login = timezone.now()
    utils.create_social_auth(user, username=user.email)
    return user


def signup(user: User, email: str, is_fake=False) -> User:
    """
    Create an account for invited users updating the invite
    in the process so it became accepted.
    """

    if hasattr(user, 'account'):
        raise HttpError(403, 'User already has an account')

    invites = Invite.objects.filter(
        email=email,
        datetime_accepted__isnull=True)

    if not is_fake and not invites.exists():
        raise HttpError(403, 'Must be invited')

    invites.update(datetime_accepted=timezone.now())

    user.email = email
    user.save()
    account = Account.objects.create(user=user)
    utils.send_verify_account_mail(
        user.email,
        user.steam_user.username,
        account.verification_token
    )
    return user


def verify_account(user: User, verification_token: str) -> User:
    """
    Mark an user account as is_verified if isn't already.
    """
    get_object_or_404(
        Account,
        user=user,
        verification_token=verification_token,
        is_verified=False)

    user.account.is_verified = True
    user.account.save()

    friendlist_add(user)
    return user


def inactivate(user: User) -> None:
    """
    Mark an user as inactive.
    Inactive users shouldn't be able to access any endpoint that requires authentication.
    """
    user.is_active = False
    user.save()
