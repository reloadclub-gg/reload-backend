from typing import List

from django.contrib.auth import get_user_model
from ninja import Form, Router
from ninja.files import UploadedFile

from accounts.api.authentication import VerifiedRequiredAuth

from . import controller
from .schemas import VALID_SUBJECTS, TicketCreateSchema, TicketSchema

User = get_user_model()

router = Router(tags=['support'])


@router.post('/tickets/', auth=VerifiedRequiredAuth(), response={201: TicketSchema})
def tickets_create(
    request,
    files: List[UploadedFile] = None,
    payload: TicketCreateSchema = Form(...),
):
    return controller.create_ticket(request.user, payload, files)


@router.get(
    '/tickets/subjects/', auth=VerifiedRequiredAuth(), response={200: List[str]}
)
def tickets_subjects_list(request):
    return VALID_SUBJECTS
