from django.contrib.auth import get_user_model
from model_bakery import baker

from core.tests import TestCase

from .. import tasks

User = get_user_model()


class FriendsTasksTestCase(TestCase):
    def test_send_user_update_to_friendlist(self):
        user = baker.make(User)
        tasks.send_user_update_to_friendlist(user.id)
