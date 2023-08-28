from django.templatetags.static import static
from ninja.errors import Http404

from accounts.tests.mixins import VerifiedAccountsMixin
from core.tests import TestCase
from notifications.api import controller, schemas
from notifications.models import Notification


class NotificationsControllerTestCase(VerifiedAccountsMixin, TestCase):
    def setUp(self):
        super().setUp()

    def test_list(self):
        Notification.create(
            'notification 1', static('icons/broadcast.png'), self.user_1.id
        )
        Notification.create(
            'notification 2', static('icons/broadcast.png'), self.user_1.id
        )
        notifications = controller.list(self.user_1)
        self.assertEqual(len(notifications), 2)

        Notification.create(
            'notification 2',
            static('icons/broadcast.png'),
            self.user_1.id,
            self.user_2.id,
        )
        notifications = controller.list(self.user_1)
        self.assertEqual(len(notifications), 3)

    def test_detail(self):
        with self.assertRaises(Http404):
            controller.detail(self.user_1, 4)

        created = Notification.create(
            'notification 1', static('icons/broadcast.png'), self.user_1.id
        )
        with self.assertRaises(Http404):
            controller.detail(self.user_2, created.id)
        notification = controller.detail(self.user_1, created.id)
        self.assertEqual(notification, created)

    def test_read(self):
        created = Notification.create(
            'notification 1', static('icons/broadcast.png'), self.user_1.id
        )
        self.assertIsNone(created.read_date)

        notification = controller.read(self.user_1, created.id, {})
        self.assertIsNone(notification.read_date)

        payload = schemas.NotificationUpdateSchema(read_date='2023-05-16T09:15:34.507Z')
        notification = controller.read(self.user_1, created.id, payload)
        self.assertIsNotNone(notification.read_date)

    def test_read_all(self):
        created1 = Notification.create(
            'notification 1', static('icons/broadcast.png'), self.user_1.id
        )
        created2 = Notification.create(
            'notification 2', static('icons/broadcast.png'), self.user_1.id
        )
        created3 = Notification.create(
            'notification 2',
            static('icons/broadcast.png'),
            self.user_1.id,
            self.user_2.id,
        )

        controller.read_all(self.user_1)
        notification1 = controller.detail(self.user_1, created1.id)
        notification2 = controller.detail(self.user_1, created2.id)
        notification3 = controller.detail(self.user_1, created3.id)
        self.assertIsNotNone(notification1.read_date)
        self.assertIsNotNone(notification2.read_date)
        self.assertIsNotNone(notification3.read_date)
