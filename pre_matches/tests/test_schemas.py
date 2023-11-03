from core.tests import TestCase

from ..api import schemas
from ..models import PreMatch
from . import mixins


class PreMatchSchemaTestCase(mixins.TeamsMixin, TestCase):
    def test_pre_match_schema(self):
        pre_match = PreMatch.create(
            self.team1.id,
            self.team2.id,
            self.team1.type_mode[0],
            self.team1.type_mode[1],
        )
        payload = schemas.PreMatchSchema.from_orm(pre_match).dict()

        expected_payload = {
            'id': pre_match.id,
            'status': pre_match.status,
            'countdown': pre_match.countdown,
            'players_ready_count': len(pre_match.players_ready),
            'players_total': len(pre_match.players),
            'user_ready': False,
            'match_type': pre_match.match_type,
            'mode': pre_match.mode,
        }
        self.assertDictEqual(payload, expected_payload)
