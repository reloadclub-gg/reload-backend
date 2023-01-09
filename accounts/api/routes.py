from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Router
from ninja.errors import HttpError

from . import controller
from .authentication import VerifiedExemptAuth, VerifiedRequiredAuth
from .schemas import (FakeSignUpSchema, FakeUserSchema, SignUpSchema,
                      UpdateUserEmailSchema, UserSchema, VerifyUserEmailSchema)

User = get_user_model()
router = Router(tags=["accounts"])


@router.post('/', auth=VerifiedExemptAuth(), response={201: UserSchema})
def signup(request, payload: SignUpSchema):
    return controller.signup(request.user, payload.email)


@router.post('fake-signup/', response={201: FakeUserSchema})
def fake_signup(request, payload: FakeSignUpSchema):
    if not settings.DEBUG:
        raise HttpError(404, 'Not found')

    user = User.objects.filter(email=payload.email)
    if not user:
        user = controller.create_fake_user(payload.email)
        user.auth.create_token()
        return controller.signup(user, payload.email, is_fake=True)

    user[0].auth.create_token()
    return user[0]


@router.delete('/', auth=VerifiedRequiredAuth())
def cancel_account(request):
    return controller.inactivate(request.user)


@router.post(
    'verify/', auth=VerifiedExemptAuth(), response={200: UserSchema, 422: UserSchema}
)
def account_verification(request, payload: VerifyUserEmailSchema):
    return controller.verify_account(request.user, payload.verification_token)


@router.get('auth/', auth=VerifiedRequiredAuth(), response=UserSchema)
def user_detail(request):
    return request.user


@router.post(
    'change-user-email/',
    auth=VerifiedRequiredAuth(),
    response={200: UserSchema, 422: UserSchema},
)
def change_user_email(request, payload: UpdateUserEmailSchema):
    return controller.change_user_email(request.user, payload.email)
