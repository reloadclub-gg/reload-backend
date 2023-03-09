from unittest import mock

from django.utils import timezone

from core.redis import RedisClient
from core.tests import TestCase

from ..models import PreMatch, PreMatchConfig, PreMatchException
from ..tasks import cancel_match_after_countdown
from . import mixins

cache = RedisClient()


class MMTasksTestCase(mixins.TeamsMixin, TestCase):
    @mock.patch('websocket.controller.match_cancel')
    def test_cancel_match_after_countdown(self, mocker):
        match = PreMatch.create(self.team1.id, self.team2.id)

        for _ in range(0, PreMatchConfig.READY_PLAYERS_MIN):
            match.set_player_lock_in()

        past_time = (timezone.now() - timezone.timedelta(seconds=32)).isoformat()
        cache.set(f'{match.cache_key}:ready_time', past_time)

        cancel_match_after_countdown(match.id)
        with self.assertRaises(PreMatchException):
            PreMatch.get_by_id(match.id)
