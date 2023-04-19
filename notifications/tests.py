from core.tests import TestCase
from matchmaking.tests.mixins import VerifiedPlayersMixin
from steam import Steam

from .api.schemas import NotificationSchema
from .models import Notification, NotificationError


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


class NotificationsSchemasTestCase(VerifiedPlayersMixin, TestCase):
    def test_notification_schema(self):
        n = Notification.create(
            content='New notification',
            avatar=Steam.build_avatar_url(self.user_1.steam_user.avatarhash, 'small'),
            to_user_id=self.user_2.id,
            from_user_id=self.user_1.id,
        )
        payload = NotificationSchema.from_orm(n).dict()
        expected_payload = {
            'id': n.id,
            'to_user_id': n.to_user_id,
            'content': n.content,
            'avatar': n.avatar,
            'create_date': n.create_date,
            'from_user_id': n.from_user_id,
            'read_date': n.read_date,
        }
        self.assertEqual(expected_payload, payload)
