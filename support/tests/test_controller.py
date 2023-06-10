import os

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from ninja.errors import HttpError

from accounts.tests.mixins import AccountOneMixin
from core.tests import TestCase

from ..api import controller, schemas


class SupportControllerTestCase(AccountOneMixin, TestCase):
    def tearDown(self):
        file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', 'upload_test_file.txt')
        with open(file_path, 'w') as f:
            f.write('')
        return super().tearDown()

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
            SimpleUploadedFile('upload_test_file.txt', b'a' * 3000000) for i in range(3)
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
            SimpleUploadedFile('upload_test_file.txt', b'a' * 3000001) for i in range(3)
        ]

        with self.assertRaises(HttpError):
            controller.create_ticket(
                self.user,
                schemas.TicketCreateSchema.from_orm(
                    {'subject': 'Ajuda', 'description': 'test'}
                ),
                files=uploaded_files,
            )
