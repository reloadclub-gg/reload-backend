from django.test import TestCase
from django.urls import reverse_lazy


class EmailViewTestCase(TestCase):
    def test_emails_view(self):
        response = self.client.get(reverse_lazy('admin:appsettings_appsettings_emails'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['title'], 'E-mails')
        self.assertListEqual(
            response.context['emails'],
            ['verify-email.html', 'inactivation-email.html', 'welcome-email.html'],
        )

    def test_email_rendered_verify_email(self):
        response = self.client.get(
            reverse_lazy(
                'admin:appsettings_appsettings_email_rendered',
                args=['verify-email.html'],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<title>ReloadClub - Falta pouco!</title>', response.content.decode()
        )

    def test_email_rendered_welcome_email(self):
        response = self.client.get(
            reverse_lazy(
                'admin:appsettings_appsettings_email_rendered',
                args=['welcome-email.html'],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<title>ReloadClub - Boas-vindas!</title>', response.content.decode()
        )

    def test_email_rendered_inactivation_email(self):
        response = self.client.get(
            reverse_lazy(
                'admin:appsettings_appsettings_email_rendered',
                args=['inactivation-email.html'],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<title>ReloadClub - Nos vemos em breve!</title>', response.content.decode()
        )
