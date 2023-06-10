from django.core.files.uploadedfile import SimpleUploadedFile
from django.templatetags.static import static

from accounts.tests.mixins import VerifiedAccountMixin
from core.tests import APIClient, TestCase

from ..api.schemas import VALID_SUBJECTS


class SupportRoutesTestCase(VerifiedAccountMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient('/api/support')
        self.user.auth.add_session()
        self.user.auth.create_token()

    def test_tickets_create(self):
        r = self.client.post(
            '/api/support/tickets/',
            data={
                'subject': 'Ajuda',
                'description': 'Some description',
                'files': SimpleUploadedFile(
                    static('tests/upload_file.txt'),
                    b'a',
                    content_type='image/txt',
                ),
            },
            format='multipart',
            HTTP_ACCEPT='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.user.auth.token}',
        )
        expected_response = {
            'subject': 'Ajuda',
            'description': 'Some description',
            'attachments_count': 1,
        }
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json(), expected_response)

    def test_tickets_subjects_list(self):
        r = self.api.call('get', '/tickets/subjects/', token=self.user.auth.token)
        self.assertEqual(r.json(), VALID_SUBJECTS)
