from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from ninja.errors import HttpError

from appsettings.services import check_invite_required
from core.redis import RedisClient
from core.utils import generate_random_string, get_ip_address
from friends.websocket import ws_friend_update_or_create
from lobbies.api.controller import player_move
from lobbies.models import Lobby
from lobbies.websocket import ws_expire_player_invites
from notifications.websocket import ws_new_notification

from .. import models, utils, websocket
from . import authorization, schemas

User = get_user_model()
cache = RedisClient()


def handle_login(request, token: str) -> models.Auth:
    auth = models.Auth.load(token)
    if not auth:
        return

    user = User.objects.filter(pk=auth.user_id).first()
    if user and (
        hasattr(request, 'verified_exempt') or authorization.is_verified(user)
    ):
        models.UserLogin.objects.update_or_create(
            user=user,
            ip_address=get_ip_address(request),
            defaults={'timestamp': timezone.now()},
        )

        user.refresh_from_db()
        request.user = user
        return auth


def handle_verify_websockets(user):
    for friend in user.account.online_friends:
        notification = friend.notify(
            _(f'Your friend {user.steam_user.username} just joined ReloadClub!'),
            user.id,
        )
        ws_new_notification(notification)

        cache.sadd(f'__friendlist:user:{friend.user.id}', user.id)

    ws_friend_update_or_create(user, 'create')


def handle_unverify_account(user):
    user.account.is_verified = False
    user.account.save()

    utils.send_verify_account_mail(
        user.email,
        user.steam_user.username,
        user.account.verification_token,
    )

    lobby = user.account.lobby
    if lobby:
        player_move(user, user.id, delete_lobby=True)

    ws_expire_player_invites(user)
    websocket.ws_update_user(user)
    ws_friend_update_or_create(user)


def handle_verify_account(user: User, verification_token: str) -> User:
    account = models.Account.objects.filter(
        user=user,
        verification_token=verification_token,
        is_verified=False,
    ).exists()

    if not account:
        raise HttpError(400, _('Invalid verification token.'))

    user.account.is_verified = True
    user.account.save()

    if not user.date_email_update:
        utils.send_welcome_mail(user.email)

    handle_verify_websockets(user)
    return user


def handle_inactivate_account(user: User) -> User:
    logout(user)
    user.inactivate()
    utils.send_inactivation_mail(user.email)
    return user


def handle_update_user_email(user: User, email: str) -> User:
    user.email = email
    user.date_email_update = timezone.now()
    user.save()
    user.account.verification_token = generate_random_string(
        length=models.Account.VERIFICATION_TOKEN_LENGTH
    )
    handle_unverify_account(user)
    return user


def get_user(user: User) -> User:
    if hasattr(user, 'account') and user.account.is_verified:
        from_offline_status = False
        if user.auth.sessions is None:
            from_offline_status = True

        user.auth.add_session()
        user.auth.persist_session()
        if from_offline_status:
            ws_friend_update_or_create(user)

        if not user.account.lobby:
            Lobby.create(user.id)

    return user


def logout(user: User) -> dict:
    ws_expire_player_invites(user)
    if hasattr(user, 'account') and user.account.lobby:
        player_move(user, user.id, delete_lobby=True)

    user.auth.expire_session(seconds=0)
    ws_friend_update_or_create(user)
    websocket.ws_user_logout(user.id)

    return {'detail': 'ok'}


def create_fake_user(email: str) -> User:
    """
    USED FOR TESTS PURPOSE ONLY!
    Creates a user that doesn't need a Steam account.
    """
    user = User.objects.create(email=email)
    auth = models.Auth(user_id=user.pk)
    auth.create_token()
    user.last_login = timezone.now()
    utils.create_social_auth(user, username=user.email)
    return user


def signup(user: User, email: str, is_fake: bool = False) -> User:
    if hasattr(user, 'account'):
        raise HttpError(403, _('User already has an account.'))

    invites = models.Invite.objects.filter(email=email, datetime_accepted__isnull=True)

    if not is_fake and (check_invite_required() and not invites.exists()):
        raise HttpError(403, _('User must be invited.'))

    invites.update(datetime_accepted=timezone.now())

    user.email = email
    user.save()
    models.Account.objects.create(user=user)
    utils.send_verify_account_mail(
        user.email,
        user.steam_user.username,
        user.account.verification_token,
    )
    return user


def update_account(user: User, payload: schemas.AccountUpdateSchema) -> User:
    if payload.email:
        return handle_update_user_email(user, payload.email)
    elif payload.inactivate:
        return handle_inactivate_account(user)
    elif payload.verification_token:
        return handle_verify_account(user, payload.verification_token)

    return user


def delete_account(user: User) -> dict:
    logout(user)
    user.delete()
    return {'status': 'deleted'}
