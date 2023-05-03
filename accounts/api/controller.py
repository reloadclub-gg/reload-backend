from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from ninja.errors import HttpError

from appsettings.services import check_invite_required
from core.utils import generate_random_string, get_ip_address
from matchmaking.models import Lobby
from websocket.tasks import (
    friendlist_add_task,
    lobby_update_task,
    user_lobby_invites_expire_task,
    user_status_change_task,
)

from .. import utils
from ..models import Account, Auth, Invite, UserLogin
from .authorization import is_verified

User = get_user_model()


def auth(user: User):
    if hasattr(user, 'account') and user.account.is_verified and not user.account.lobby:
        if user.auth.sessions is None:
            user.auth.add_session()

        Lobby.create(user.id)

        user.auth.remove_session()
        if user.auth.sessions == 0:
            user.auth.expire_session(0)

    return user


def login(request, token: str) -> Auth:
    """
    Checks if there is any existing user for the given auth token and
    creates/update an UserLogin for that user with the request IP address.

    :params request Request: The request object.
    """
    auth = Auth.load(token)

    if not auth:
        return

    user = User.objects.filter(pk=auth.user_id).first()

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
    user_lobby_invites_expire_task.delay(user.id)
    lobby = user.account.lobby
    if lobby:
        new_lobby = Lobby.move(user.id, user.id, remove=True)
        if new_lobby:
            lobby_update_task.delay([new_lobby.id])

    user.auth.expire_session(seconds=0)
    user_status_change_task.delay(user.id)

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
        raise HttpError(403, _('User already has an account.'))

    invites = Invite.objects.filter(email=email, datetime_accepted__isnull=True)

    if not is_fake and (check_invite_required() and not invites.exists()):
        raise HttpError(403, _('User must be invited.'))

    invites.update(datetime_accepted=timezone.now())

    user.email = email
    user.save()
    Account.objects.create(user=user)
    utils.send_verify_account_mail(
        user.email, user.steam_user.username, user.account.verification_token
    )
    return user


def verify_account(user: User, verification_token: str) -> User:
    """
    Mark an user account as is_verified if isn't already.
    """
    account = Account.objects.filter(
        user=user, verification_token=verification_token, is_verified=False
    ).exists()

    if not account:
        raise HttpError(400, _('Invalid verification token.'))

    user.account.is_verified = True
    user.account.save()

    if user.auth.sessions is None:
        # we just need to create a session to create a lobby
        user.auth.add_session()
        user.auth.persist_session()

    if not user.account.lobby:
        # we need to create a session in order to create a lobby
        if user.auth.sessions is None:
            user.auth.add_session()
            user.auth.persist_session()

        Lobby.create(user.id)

        # then we can remove the session
        user.auth.remove_session()
        if user.auth.sessions == 0:
            user.auth.expire_session(0)

    if not user.date_email_update:
        utils.send_welcome_mail(user.email)

    friends_ids = []
    for friend in user.account.online_friends:
        friends_ids.append(friend.id)
        notification = friend.notify(
            _(f'Your friend {user.steam_user.username} just joined ReloadClub!'),
            user.id,
        )

    friendlist_add_task.delay(user.id, groups=friends_ids)
    return user


def inactivate(user: User) -> User:
    """
    Mark an user as inactive.
    Inactive users shouldn't be able to access any endpoint that requires authentication.
    """
    logout(user)
    user.inactivate()
    utils.send_inactivation_mail(user.email)
    return user


def update_email(user: User, email: str) -> User:
    """
    Change user email and inactive user
    """
    user.email = email
    user.date_email_update = timezone.now()
    user.save()
    user.account.verification_token = generate_random_string(
        length=Account.VERIFICATION_TOKEN_LENGTH
    )
    user.account.is_verified = False
    user.account.save()

    utils.send_verify_account_mail(
        user.email, user.steam_user.username, user.account.verification_token
    )

    user_status_change_task.delay(user.id)
    lobby = user.account.lobby
    if lobby:
        lobby.move(user.id, user.id, remove=True)
        if lobby.players_count > 0:
            lobby_update_task.delay([lobby.id])

    return user
