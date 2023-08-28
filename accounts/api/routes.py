from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Router
from ninja.errors import Http404

from matches.api.schemas import MatchSchema

from . import controller
from .authentication import VerifiedExemptAuth, VerifiedRequiredAuth
from .schemas import (
    FakeSignUpSchema,
    FakeUserSchema,
    SignUpSchema,
    UpdateUserEmailSchema,
    UserSchema,
    VerifyUserEmailSchema,
)

User = get_user_model()
router = Router(tags=["accounts"])


@router.post('/', auth=VerifiedExemptAuth(), response={201: UserSchema})
def signup(request, payload: SignUpSchema):
    return controller.signup(request.user, payload.email)


@router.post('fake-signup/', response={201: FakeUserSchema})
def fake_signup(request, payload: FakeSignUpSchema):
    if not settings.DEBUG:
        raise Http404()

    user = User.objects.filter(email=payload.email)
    if not user:
        user = controller.create_fake_user(payload.email)
        user.auth.create_token()
        return controller.signup(user, payload.email, is_fake=True)

    user[0].auth.create_token()
    return controller.auth(user[0], from_fake_signup=True)


@router.patch('inactivate/', auth=VerifiedRequiredAuth(), response={200: UserSchema})
def account_inactivation(request):
    return controller.inactivate(request.user)


@router.delete('/', auth=VerifiedRequiredAuth(), response={200: dict})
def account_cancel(request):
    return controller.delete_account(request.user)


@router.post(
    'verify/', auth=VerifiedExemptAuth(), response={200: UserSchema, 422: UserSchema}
)
def account_verification(request, payload: VerifyUserEmailSchema):
    return controller.verify_account(request.user, payload.verification_token)


@router.get('auth/', auth=VerifiedExemptAuth(), response=UserSchema)
def user_detail(request):
    return controller.auth(request.user)


@router.patch(
    'update-email/',
    auth=VerifiedExemptAuth(),
    response={200: UserSchema, 422: UserSchema},
)
def update_email(request, payload: UpdateUserEmailSchema):
    return controller.update_email(request.user, payload.email)


@router.patch('logout/', auth=VerifiedExemptAuth(), response={200: dict})
def logout(request):
    return controller.logout(request.user)


@router.get('{user_id}/matches/', response={200: List[MatchSchema]})
def user_matches(request, user_id: int):
    return controller.user_matches(user_id)
