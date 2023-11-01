import requests
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from ninja.errors import HttpError

from appsettings.models import AppSettings
from appsettings.services import check_invite_required
from core.redis import redis_client_instance as cache
from core.utils import generate_random_string, get_ip_address
from friends.tasks import (
    add_user_to_friends_friendlist,
    notify_friends_about_signup,
    send_user_update_to_friendlist,
)
from lobbies.api.controller import handle_player_move
from lobbies.models import Lobby, LobbyException
from lobbies.websocket import ws_expire_player_invites
from matches.models import BetaUser, Match
from steam import SteamClient

from .. import tasks, utils, websocket
from ..models import Account, Auth, Invite, SteamUser, UserLogin
from .authorization import is_verified

User = get_user_model()


def handle_verify_tasks(user: User):
    lang = get_language()
    notify_friends_about_signup.delay(user.id, lang)
    add_user_to_friends_friendlist.delay(user.id)
    send_user_update_to_friendlist.delay(user.id, action='create')


def auth(user: User, from_fake_signup=False) -> User:
    """
    Authenticate user, add session and possibly update friends and create lobby.
    """

    if not is_verified(user):
        return user

    if AppSettings.get('Beta Required', False):
        is_beta = BetaUser.objects.filter(email=user.email).exists()
        if not is_beta:
            raise HttpError(401, _('User must be invited.'))

    from_offline_status = user.auth.sessions is None

    # Adding and persisting session
    if not from_fake_signup:
        user.add_session()
        user.auth.persist_session()

        # Creating lobby if user does not have one
        if not user.account.lobby:
            Lobby.create(user.id)

    # Updating friends if user status has changed from offline
    if from_offline_status:
        send_user_update_to_friendlist.delay(user.id)

    return user


def login(request, token: str) -> Auth:
    """
    Attempts to authenticate a user with a given auth token.

    If a User with the token exists and the request is verified exempt or the user is verified,
    an UserLogin is updated or created for the user with the request's IP address.

    Returns an Auth object if successful, otherwise None.
    """
    auth = Auth.load(token)

    if not auth:
        return None

    try:
        user = User.objects.get(pk=auth.user_id)
    except User.DoesNotExist:
        return None

    if not hasattr(request, 'verified_exempt') and not is_verified(user):
        return None

    UserLogin.objects.update_or_create(
        user=user,
        ip_address=get_ip_address(request),
        defaults={'timestamp': timezone.now()},
    )

    user.refresh_from_db()
    request.user = user

    return auth


def logout(user: User) -> dict:
    """
    Logout user.
    """

    # Expiring player invites
    ws_expire_player_invites(user)

    # If user has an account
    if hasattr(user, 'account'):
        try:
            handle_player_move(user, user.id, delete_lobby=True)
        except LobbyException as e:
            raise HttpError(400, e)

        # Update or create friend
        send_user_update_to_friendlist.delay(user.id)

    # Expiring user session
    user.logout()

    # Send websocket logout message
    websocket.ws_user_logout(user.id)

    # Deleting user from friend list cache
    cache.delete(f'__friendlist:user:{user.id}')

    return {'detail': 'Logout successful.'}


def create_fake_user(email: str) -> User:
    """
    USED FOR TESTS PURPOSE ONLY!
    Creates a user that doesn't need a Steam account.
    """
    user = User.objects.create(email=email)
    Auth(user_id=user.pk, force_token_create=True)
    utils.create_social_auth(user, username=user.email)
    return user


def signup(user: User, email: str, is_fake: bool = False) -> User:
    """
    Create an account for invited users updating the invite
    in the process so it became accepted.
    """
    try:
        if user.account:
            raise HttpError(403, _('User already has an account.'))
    except Account.DoesNotExist:
        pass

    if AppSettings.get('Beta Required', False):
        is_beta = BetaUser.objects.filter(email=email).exists()
        if not is_beta:
            raise HttpError(401, _('User must be invited.'))
    else:
        invites = Invite.objects.filter(email=email, datetime_accepted__isnull=True)
        if not is_fake and check_invite_required() and not invites.exists():
            raise HttpError(401, _('User must be invited.'))

        invites.update(datetime_accepted=timezone.now())

    with transaction.atomic():
        user.email = email
        user.save()
        Account.objects.create(user=user)

    if not is_fake:
        tasks.send_verify_email.delay(
            user.email,
            user.account.username,
            user.account.verification_token,
        )

    # Refresh user instance with updated related account
    user.refresh_from_db()

    return user


def verify_account(user: User, verification_token: str) -> User:
    """
    Mark an user account as is_verified if isn't already.
    """
    try:
        account = Account.objects.get(
            user=user,
            verification_token=verification_token,
            is_verified=False,
        )
    except Account.DoesNotExist:
        raise HttpError(400, _('Invalid verification token.'))

    account.is_verified = True
    account.save()

    if not user.date_email_update:
        tasks.send_welcome_email.delay(user.email)
        handle_verify_tasks(user)
    else:
        send_user_update_to_friendlist.delay(user.id)

    # Refresh user instance with updated related account
    user.refresh_from_db()

    return user


def inactivate(user: User) -> User:
    """
    Mark an user as inactive.
    Inactive users shouldn't be able to access any endpoint that requires authentication.
    """
    logout(user)
    user.inactivate()
    tasks.send_inactivation_mail.delay(user.email)
    return user


def update_email(user: User, email: str) -> User:
    """
    Change user email and set user as unverified.
    """
    with transaction.atomic():
        user.email = email
        user.date_email_update = timezone.now()
        user.save()
        user.account.verification_token = generate_random_string(
            length=Account.VERIFICATION_TOKEN_LENGTH
        )
        user.account.is_verified = False
        user.account.save()

    tasks.send_verify_email.delay(
        user.email,
        user.account.username,
        user.account.verification_token,
    )

    # Refresh user instance with updated related account
    user.refresh_from_db()

    websocket.ws_update_user(user)
    if user.account.lobby:
        try:
            handle_player_move(user, user.id, delete_lobby=True)
        except LobbyException as e:
            raise HttpError(400, e)

    return user


def user_matches(user_id: int) -> Match:
    account = get_object_or_404(Account, user__id=user_id)
    return account.get_matches_played()


def delete_account(user: User) -> dict:
    logout(user)
    user.delete()
    return {'status': 'deleted'}


def send_invite(user: User, email: str) -> Invite:
    invite = user.account.invite_set.create(email=email)
    tasks.send_invite_mail.delay(email, user.account.username)
    return invite


def steam_sync(user: User) -> User:
    new_data = SteamClient.get_player_data(user.account.steamid)
    steam_user = SteamUser(user_id=user.id, **new_data)
    steam_user.save()
    user.account.username = steam_user.username
    user.account.save()
    user.refresh_from_db()
    return user
