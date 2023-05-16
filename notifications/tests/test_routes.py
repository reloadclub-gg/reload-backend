from django.templatetags.static import static

from core.tests import APIClient, TestCase
from matchmaking.tests.mixins import VerifiedPlayersMixin
from notifications.api.schemas import NotificationSchema
from notifications.models import Notification


class NotificationsRoutesTestCase(VerifiedPlayersMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient('/api/notifications')
        self.user_1.auth.create_token()
        self.user_2.auth.create_token()

    def test_list(self):
        r = self.api.call('get', '/', token=self.user_1.auth.token)
        self.assertEqual(r.json(), [])

        created = Notification.create(
            'notification 1', static('icons/broadcast.png'), self.user_1.id
        )

        r = self.api.call('get', '/', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)
        self.assertEqual(r.json(), [NotificationSchema.from_orm(created).dict()])

    def test_detail(self):
        r = self.api.call('get', '/1', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 404)

        created = Notification.create(
            'notification 1', static('icons/broadcast.png'), self.user_1.id
        )

        r = self.api.call('get', f'/{created.id}', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), NotificationSchema.from_orm(created).dict())

    def test_read(self):
        created = Notification.create(
            'notification 1', static('icons/broadcast.png'), self.user_1.id
        )
        r = self.api.call('get', f'/{created.id}', token=self.user_1.auth.token)
        self.assertIsNone(r.json().get('read_date'))

        r = self.api.call(
            'patch',
            f'/{created.id}',
            token=self.user_1.auth.token,
            data={'read_date': '2023-05-16T09:15:34.507Z'},
        )
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.json().get('read_date'))

    def test_read_all(self):
        Notification.create(
            'notification 1', static('icons/broadcast.png'), self.user_1.id
        )
        Notification.create(
            'notification 2', static('icons/broadcast.png'), self.user_1.id
        )

        r = self.api.call('patch', '/read-all', token=self.user_1.auth.token)
        self.assertEqual(r.status_code, 200)
        assert all(
            item.read_date is not None for item in self.user_1.account.notifications
        )
        assert all(item.get('read_date') is not None for item in r.json())
