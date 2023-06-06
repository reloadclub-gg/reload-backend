from core.tests import TestCase

from ..api import schemas
from ..models import PreMatch, PreMatchConfig
from . import mixins


class PreMatchSchemaTestCase(mixins.TeamsMixin, TestCase):
    def test_pre_match_schema(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        payload = schemas.PreMatchSchema.from_orm(pre_match).dict()

        expected_payload = {
            'id': pre_match.id,
            'state': list(PreMatchConfig.STATES.keys())[
                list(PreMatchConfig.STATES.values()).index(pre_match.state)
            ],
            'countdown': pre_match.countdown,
            'players_ready_count': len(pre_match.players_ready),
            'players_total': len(pre_match.players),
            'user_ready': False,
        }
        self.assertDictEqual(payload, expected_payload)
