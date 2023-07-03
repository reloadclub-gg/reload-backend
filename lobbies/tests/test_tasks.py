from unittest import mock

from django.utils import timezone

from core.redis import RedisClient
from core.tests import TestCase
from pre_matches.tests.mixins import TeamsMixin

from .. import models, tasks

cache = RedisClient()


class LobbyTasksTestCase(TeamsMixin, TestCase):
    def test_clear_dodges(self):
        player = models.Player.create(self.user_1.id)
        tasks.clear_dodges()
        self.assertEqual(player.dodges, 0)
        today = timezone.now().isoformat()
        two_weeks_ago = (timezone.now() - timezone.timedelta(weeks=2)).isoformat()

        cache.zadd(
            f'{player.cache_key}:dodges',
            {two_weeks_ago: 1680800659.26437},
        )
        tasks.clear_dodges()
        self.assertEqual(player.dodges, 0)

        cache.zadd(
            f'{player.cache_key}:dodges',
            {today: 1680800759.26437},
        )
        tasks.clear_dodges()
        self.assertEqual(player.dodges, 1)

    @mock.patch('lobbies.tasks.ws_queue_tick')
    def test_queue_tick(self, mock_queue_tick):
        tasks.queue_tick(self.user_1.account.lobby.id)
        mock_queue_tick.assert_not_called()

        self.user_1.account.lobby.start_queue()
        tasks.queue_tick(self.user_1.account.lobby.id)
        mock_queue_tick.assert_called_once_with(self.user_1.account.lobby)
