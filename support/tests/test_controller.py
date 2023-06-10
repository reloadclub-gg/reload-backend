from django.core.files.uploadedfile import SimpleUploadedFile
from django.templatetags.static import static
from ninja.errors import HttpError

from accounts.tests.mixins import AccountOneMixin
from core.tests import TestCase

from ..api import controller, schemas


class SupportControllerTestCase(AccountOneMixin, TestCase):
    def test_create_ticket(self):
        ticket = controller.create_ticket(
            self.user,
            schemas.TicketCreateSchema.from_orm(
                {'subject': 'Ajuda', 'description': 'test'}
            ),
        )

        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.subject, 'Ajuda')

    def test_create_ticket_with_attachments(self):
        uploaded_files = [
            SimpleUploadedFile(
                static('tests/upload_file.txt'),
                b'a' * 3000000,
                content_type='image/txt',
            )
            for i in range(3)
        ]
        ticket = controller.create_ticket(
            self.user,
            schemas.TicketCreateSchema.from_orm(
                {'subject': 'Ajuda', 'description': 'test'}
            ),
            files=uploaded_files,
        )

        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.subject, 'Ajuda')

    def test_create_ticket_with_attachments_size_exceeded(self):
        uploaded_files = [
            SimpleUploadedFile(
                static('tests/upload_file.txt'),
                b'a' * 3000001,
                content_type='image/txt',
            )
            for i in range(3)
        ]

        with self.assertRaises(HttpError):
            controller.create_ticket(
                self.user,
                schemas.TicketCreateSchema.from_orm(
                    {'subject': 'Ajuda', 'description': 'test'}
                ),
                files=uploaded_files,
            )
