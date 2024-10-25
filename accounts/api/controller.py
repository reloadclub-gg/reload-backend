import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from ninja.errors import HttpError

from appsettings.services import (
    check_alpha_required,
    check_beta_required,
    check_invite_required,
    maintenance_window,
)
from core.redis import redis_client_instance as cache
from core.utils import generate_random_string, get_ip_address
from friends.websocket import ws_friends_add
from lobbies.api.controller import handle_player_move
from lobbies.models import Lobby, LobbyException
from lobbies.websocket import ws_expire_player_invites
from matches.models import BetaUser, Match
from steam import SteamClient
from store.models import Item, UserStore

from .. import tasks, utils, websocket
from ..models import Account, Auth, Invite, SteamUser, UserLogin
from .authorization import is_verified

User = get_user_model()


def check_beta(user, email: str = None):
    email = email or user.email
    beta_required = check_beta_required()
    if beta_required:
        is_beta = BetaUser.objects.filter(email=email).exists()
        if not is_beta and not user.is_alpha:
            raise HttpError(401, _("User must be invited."))


def check_alpha(user):
    alpha_required = check_alpha_required()
    if alpha_required and not user.is_alpha:
        raise HttpError(401, _("User must be invited."))


def check_invite(user, email: str = None, is_fake: bool = False):
    email = email or user.email
    invite_required = check_invite_required()
    if invite_required:
        invites = Invite.objects.filter(email=email, datetime_accepted__isnull=True)
        if not is_fake and not invites.exists():
            raise HttpError(401, _("User must be invited."))
        invites.update(datetime_accepted=timezone.now())


def auth(user: User, from_fake_signup=False) -> User:
    """
    Authenticate user, add session and possibly update friends and create lobby.
    """

    if not is_verified(user) or not user.is_active:
        return user

    from_offline_status = user.auth.sessions is None

    # Adding and persisting session
    if not from_fake_signup and not maintenance_window():
        check_beta(user, user.email)
        check_alpha(user)

        user.add_session()
        user.auth.persist_session()

        # Creating lobby if user does not have one
        if not user.account.lobby:
            Lobby.create(user.id)

    # Updating friends if user status has changed from offline
    if from_offline_status:
        websocket.ws_update_status_on_friendlist(user)

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

    if not hasattr(request, "verified_exempt") and (
        not is_verified(user) or not user.is_active
    ):
        return None

    UserLogin.objects.update_or_create(
        user=user,
        ip_address=get_ip_address(request),
        defaults={"timestamp": timezone.now()},
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
    if hasattr(user, "account") and user.account.lobby:
        try:
            handle_player_move(user, user.id, delete_lobby=True)
        except LobbyException as e:
            raise HttpError(400, e)

        # Update its friendlist
        websocket.ws_update_status_on_friendlist(user)

    # Expiring user session
    user.logout()

    # Send websocket logout message
    websocket.ws_user_logout(user.id)

    # Deleting user from friend list cache
    cache.delete(f"__friendlist:user:{user.id}")

    return {"detail": "Logout successful."}


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
            raise HttpError(403, _("User already has an account."))
    except Account.DoesNotExist:
        pass

    if not email or email == "":
        raise HttpError(400, _("Unable to create account."))

    if not is_fake:
        check_beta(user, email)
        check_alpha(user)
        check_invite(user, email, is_fake)

    try:
        with transaction.atomic():
            user.email = email
            user.save()
            Account.objects.create(user=user)
    except IntegrityError as e:
        logging.error(e)
        raise HttpError(400, _("Unable to create account."))

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
        raise HttpError(400, _("Invalid verification token."))

    account.is_verified = True
    account.save()

    # Refresh user instance with updated related account
    user.refresh_from_db()

    if not user.date_email_update:
        tasks.send_welcome_email.delay(user.email)

        # give starter and free items
        starter_items = Item.objects.filter(Q(is_starter=True) | Q(price=0))
        for item in starter_items:
            user.useritem_set.create(item=item, in_use=item.is_starter)

        if settings.APP_GLOBAL_FRIENDSHIP:
            for user in User.active_verified_users([account.user.id]):
                ws_friends_add(account.user, user)

        # create user store
        UserStore.populate(user)

    return user


def inactivate(user: User) -> User:
    """
    Mark an user as inactive.
    Inactive users shouldn't be able to access any endpoint that requires authentication.
    """

    if (
        user.account.get_match()
        or user.account.pre_match
        or (user.account.lobby and user.account.lobby.queue)
    ):
        raise HttpError(
            400,
            _(
                "You can't inactivate or delete your account while in queueing or in a match."
            ),
        )

    logout(user)
    user.inactivate()
    tasks.send_inactivation_mail.delay(user.email)
    return user


def update_email(user: User, email: str) -> User:
    """
    Change user email and set user as unverified.
    """
    if not email or email == "":
        raise HttpError(400, _("Unable to update e-mail."))

    try:
        with transaction.atomic():
            user.email = email
            user.date_email_update = timezone.now()
            user.save()
            user.account.verification_token = generate_random_string(
                length=Account.VERIFICATION_TOKEN_LENGTH
            )
            user.account.is_verified = False
            user.account.save()
    except IntegrityError as e:
        logging.error(e)
        raise HttpError(400, _("Unable to update e-mail."))

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
    if (
        user.account.get_match()
        or user.account.pre_match
        or (user.account.lobby and user.account.lobby.queue)
    ):
        raise HttpError(
            400,
            _(
                "You can't inactivate or delete your account while in queueing or in a match."
            ),
        )

    logout(user)
    user.delete()
    return {"status": "deleted"}


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
