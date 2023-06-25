from unittest import mock

from django.templatetags.static import static

from core.tests import TestCase
from matchmaking.tests.mixins import VerifiedPlayersMixin
from notifications.models import Notification, NotificationError, SystemNotification
from steam import Steam


class NotificationsNotificationModelTestCase(VerifiedPlayersMixin, TestCase):
    def test_create(self):
        first_created_id = None

        for index in range(0, 10):
            created = Notification.create(
                content='New notification',
                avatar=Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'small'
                ),
                to_user_id=self.user_2.id,
                from_user_id=self.user_1.id,
            )
            n = Notification.get_by_id(created.id)
            if index == 0:
                first_created_id = n.id
            self.assertEqual(n.content, created.content)
            self.assertEqual(n.id, created.id)
            self.assertEqual(
                len(Notification.get_all_by_user_id(self.user_2.id)), index + 1
            )

        created = Notification.create(
            content='New notification',
            avatar=Steam.build_avatar_url(self.user_1.steam_user.avatarhash, 'small'),
            to_user_id=self.user_2.id,
            from_user_id=self.user_1.id,
        )
        self.assertEqual(len(Notification.get_all_by_user_id(self.user_2.id)), 10)
        with self.assertRaises(NotificationError):
            Notification.get_by_id(first_created_id)

    def test_get_all_by_user_id(self):
        Notification.create(
            content='New notification',
            avatar=Steam.build_avatar_url(self.user_1.steam_user.avatarhash, 'small'),
            to_user_id=self.user_2.id,
            from_user_id=self.user_1.id,
        )
        results = Notification.get_all_by_user_id(self.user_2.id)
        self.assertEqual(len(results), 1)

        for _ in range(1, 9):
            Notification.create(
                content='New notification',
                avatar=Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'small'
                ),
                to_user_id=self.user_2.id,
                from_user_id=self.user_1.id,
            )

        results = Notification.get_all_by_user_id(self.user_2.id)
        self.assertEqual(len(results), 9)

    def test_auto_id(self):
        for _ in range(0, 10):
            Notification.create(
                content='New notification',
                avatar=Steam.build_avatar_url(
                    self.user_1.steam_user.avatarhash, 'small'
                ),
                to_user_id=self.user_2.id,
                from_user_id=self.user_1.id,
            )
        self.assertEqual(Notification.get_auto_id(), 10)

    def test_save(self):
        auto_id = Notification.incr_auto_id()
        n = Notification(
            id=auto_id,
            content='New notification',
            avatar=Steam.build_avatar_url(self.user_1.steam_user.avatarhash, 'small'),
            to_user_id=self.user_2.id,
            from_user_id=self.user_1.id,
        )
        self.assertEqual(len(Notification.get_all_by_user_id(self.user_2.id)), 0)

        created, object = n.save()
        self.assertTrue(created)
        self.assertEqual(len(Notification.get_all_by_user_id(self.user_2.id)), 1)

        created, object = n.save()
        self.assertFalse(created)
        self.assertEqual(len(Notification.get_all_by_user_id(self.user_2.id)), 1)

        n.from_user_id = self.user_3.id
        n.save()
        self.assertEqual(Notification.get_by_id(n.id).from_user_id, self.user_3.id)

    def test_mark_as_read(self):
        n = Notification.create(
            content='New notification',
            avatar=Steam.build_avatar_url(self.user_1.steam_user.avatarhash, 'small'),
            to_user_id=self.user_2.id,
            from_user_id=self.user_1.id,
        )

        self.assertIsNone(n.read_date)
        n.mark_as_read()
        self.assertIsNotNone(n.read_date)

    def test_create_system_notifications(self):
        notifications = Notification.create_system_notifications(
            content='System notification',
            avatar=static('icons/broadcast.png'),
            to_user_ids=[self.user_1.id, self.user_2.id, self.user_4.id],
        )
        self.assertEqual(len(notifications), 3)

        n1 = notifications[0]
        n2 = notifications[1]
        n3 = notifications[2]

        self.assertEqual(n1.to_user_id, self.user_1.id)
        self.assertEqual(n2.to_user_id, self.user_2.id)
        self.assertEqual(n3.to_user_id, self.user_4.id)


class NotificationsSystemNotificationModelTestCase(VerifiedPlayersMixin, TestCase):
    @mock.patch('notifications.models.ws_send')
    def test_system_notification_to_users_changed_signal(self, mock_ws_send):
        n = SystemNotification(content='Sys Notification')
        n.save()
        n.to_users.set([self.user_1, self.user_2])

        user1_notifications = Notification.get_all_by_user_id(self.user_1.id)
        user2_notifications = Notification.get_all_by_user_id(self.user_2.id)

        self.assertEqual(len(user1_notifications), 1)
        self.assertEqual(len(user2_notifications), 1)
        self.assertEqual(mock_ws_send.call_count, 2)
