from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja.errors import HttpError

from appsettings.services import check_invite_required
from core.utils import generate_random_string, get_ip_address
from websocket.controller import friendlist_add, lobby_update, user_status_change

from .. import utils
from ..models import Account, Auth, Invite, UserLogin
from .authorization import is_verified

User = get_user_model()


def login(request, token: str) -> Auth:
    """
    Checks if there is any existing user for the given auth token and
    creates/update an UserLogin for that user with the request IP address.

    :params request Request: The request object.
    """
    auth = Auth.load(token)

    if not auth:
        return

    user = User.objects.filter(pk=auth.user_id, is_active=True).first()

    if user and (hasattr(request, 'verified_exempt') or is_verified(user)):
        UserLogin.objects.update_or_create(
            user=user,
            ip_address=get_ip_address(request),
            defaults={'timestamp': timezone.now()},
        )

        user.refresh_from_db()
        request.user = user

        return auth


def logout(user: User) -> User:
    lobby = user.account.lobby
    if lobby:
        lobby.move(user.id, user.id, remove=True)
        if lobby.players_count > 0:
            lobby_update(lobby)

    user.auth.expire_session(seconds=0)
    user.save()

    user_status_change(user)

    return user


def create_fake_user(email: str) -> User:
    """
    USED FOR TESTS PURPOSE ONLY!
    Creates a user that doesn't need a Steam account.
    """
    user = User.objects.create(email=email)
    auth = Auth(user_id=user.pk)
    auth.create_token()
    user.last_login = timezone.now()
    utils.create_social_auth(user, username=user.email)
    return user


def signup(user: User, email: str, is_fake: bool = False) -> User:
    """
    Create an account for invited users updating the invite
    in the process so it became accepted.
    """

    if hasattr(user, 'account'):
        raise HttpError(403, 'User already has an account')

    invites = Invite.objects.filter(email=email, datetime_accepted__isnull=True)

    if not is_fake and (check_invite_required() and not invites.exists()):
        raise HttpError(403, 'Must be invited')

    invites.update(datetime_accepted=timezone.now())

    user.email = email
    user.save()
    account = Account.objects.create(user=user)
    utils.send_verify_account_mail(
        user.email, user.steam_user.username, account.verification_token
    )
    return user


def verify_account(user: User, verification_token: str) -> User:
    """
    Mark an user account as is_verified if isn't already.
    """
    get_object_or_404(
        Account, user=user, verification_token=verification_token, is_verified=False
    )

    user.account.is_verified = True
    user.account.save()

    friendlist_add(user)
    return user


def inactivate(user: User) -> None:
    """
    Mark an user as inactive.
    Inactive users shouldn't be able to access any endpoint that requires authentication.
    """
    logout(user)

    user.is_active = False
    user.save()


def update_email(user: User, email: str) -> User:
    """
    Change user email and inactive user
    """
    user.email = email
    user.save()
    user.account.verification_token = generate_random_string(
        length=Account.VERIFICATION_TOKEN_LENGTH
    )
    user.account.is_verified = False
    user.account.save()

    utils.send_verify_account_mail(
        user.email, user.steam_user.username, user.account.verification_token
    )

    user_status_change(user)
    lobby = user.account.lobby
    if lobby:
        lobby.move(user.id, user.id, remove=True)
        if lobby.players_count > 0:
            lobby_update(lobby)

    return user
