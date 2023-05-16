from core.tests import TestCase
from matchmaking.tests.mixins import VerifiedPlayersMixin
from notifications.api.schemas import NotificationSchema
from notifications.models import Notification
from steam import Steam


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
            'create_date': n.create_date.isoformat(),
            'from_user_id': n.from_user_id,
            'read_date': n.read_date.isoformat() if n.read_date else None,
        }
        self.assertEqual(expected_payload, payload)
