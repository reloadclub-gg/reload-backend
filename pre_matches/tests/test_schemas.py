from core.tests import TestCase

from ..api import schemas
from ..models import PreMatch
from . import mixins


class PreMatchSchemaTestCase(mixins.TeamsMixin, TestCase):
    def test_pre_match_schema(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id, self.team1.mode)
        payload = schemas.PreMatchSchema.from_orm(pre_match).dict()

        expected_payload = {
            'id': pre_match.id,
            'ready': pre_match.ready,
            'countdown': pre_match.countdown,
            'players_ready_count': len(pre_match.players_ready),
            'players_total': len(pre_match.players),
            'user_ready': False,
            'mode': pre_match.mode,
        }
        self.assertDictEqual(payload, expected_payload)
