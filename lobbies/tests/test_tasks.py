from django.utils import timezone

from core.redis import RedisClient
from core.tests import TestCase
from pre_matches.tests.mixins import TeamsMixin

from ..models import Player
from ..tasks import clear_dodges

cache = RedisClient()


class LobbyTasksTestCase(TeamsMixin, TestCase):
    def test_clear_dodges(self):
        player = Player.create(self.user_1.id)
        clear_dodges()
        self.assertEqual(player.dodges, 0)
        today = timezone.now().isoformat()
        two_weeks_ago = (timezone.now() - timezone.timedelta(weeks=2)).isoformat()

        cache.zadd(
            f'{player.cache_key}:dodges',
            {two_weeks_ago: 1680800659.26437},
        )
        clear_dodges()
        self.assertEqual(player.dodges, 0)

        cache.zadd(
            f'{player.cache_key}:dodges',
            {today: 1680800759.26437},
        )
        clear_dodges()
        self.assertEqual(player.dodges, 1)
