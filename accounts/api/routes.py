from django.conf import settings
from django.contrib.auth import get_user_model
from ninja import Router
from ninja.errors import Http404

from . import controller, schemas
from .authentication import VerifiedExemptAuth, VerifiedRequiredAuth

User = get_user_model()
router = Router(tags=["accounts"])


@router.post('fake-signup/', response={201: schemas.FakeUserSchema})
def fake_signup(request, payload: schemas.FakeSignUpSchema):
    if not settings.DEBUG:
        raise Http404()

    user = User.objects.filter(email=payload.email)
    if not user:
        user = controller.create_fake_user(payload.email)
        user.auth.create_token()
        return controller.signup(user, payload.email, is_fake=True)

    user[0].auth.create_token()
    return controller.get_user(user[0])


@router.patch('logout/', auth=VerifiedExemptAuth(), response={200: dict})
def logout(request):
    return controller.logout(request.user)


@router.post('/', auth=VerifiedExemptAuth(), response={201: schemas.UserSchema})
def signup(request, payload: schemas.SignUpSchema):
    return controller.signup(request.user, payload.email)


@router.get('/', auth=VerifiedExemptAuth(), response={200: schemas.UserSchema})
def user_detail(request):
    return controller.get_user(request.user)


@router.patch('/', auth=VerifiedRequiredAuth(), response={200: schemas.UserSchema})
def account_update(request, payload: schemas.AccountUpdateSchema):
    return controller.update_account(request.user, payload)


@router.delete('/', auth=VerifiedRequiredAuth(), response={200: dict})
def accaount_cancel(request):
    return controller.delete_account(request.user)
