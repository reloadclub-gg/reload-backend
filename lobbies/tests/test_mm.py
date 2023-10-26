import time
from unittest import mock

from django.conf import settings
from django.test import override_settings
from model_bakery import baker

from core.tests import APIClient, TestCase
from lobbies.tasks import queue
from matches.models import Match, Server
from pre_matches.models import PreMatch, PreMatchException, Team
from pre_matches.tasks import cancel_match_after_countdown

from .mixins import LobbiesMixin


class LobbiesMMTestCase(LobbiesMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.lobby_api = APIClient('/api/lobbies')
        self.pre_match_api = APIClient('/api/pre-matches')

    @override_settings(TEAM_READY_PLAYERS_MIN=2)
    @mock.patch(
        'pre_matches.api.controller.tasks.cancel_match_after_countdown.apply_async'
    )
    def test_teamed_mm_routes(self, mock_cancel_match_task):
        queue()

        # lobby 1 & 2 preparation
        r = self.lobby_api.call(
            'post',
            '/invites',
            data={
                'lobby_id': self.lobby1.id,
                'from_user_id': self.user_1.id,
                'to_user_id': self.user_2.id,
            },
            token=self.user_1.auth.token,
        )
        queue()
        self.assertEqual(r.status_code, 201)
        invite_id = r.json().get('id')

        r = self.lobby_api.call(
            'delete',
            f'/invites/{invite_id}',
            data={'accept': True},
            token=self.user_2.auth.token,
        )
        queue()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.lobby1.players_count, 2)
        self.assertEqual(self.lobby2.players_count, 0)

        # lobby 3 & 4 preparation
        r = self.lobby_api.call(
            'post',
            '/invites',
            data={
                'lobby_id': self.lobby3.id,
                'from_user_id': self.user_3.id,
                'to_user_id': self.user_4.id,
            },
            token=self.user_3.auth.token,
        )
        queue()
        self.assertEqual(r.status_code, 201)
        invite_id = r.json().get('id')

        r = self.lobby_api.call(
            'delete',
            f'/invites/{invite_id}',
            data={'accept': True},
            token=self.user_4.auth.token,
        )
        queue()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.lobby3.players_count, 2)
        self.assertEqual(self.lobby4.players_count, 0)

        # lobby 1 & 2 queue
        self.assertIsNone(self.lobby1.queue)
        r = self.lobby_api.call(
            'patch',
            f'/{self.lobby1.id}',
            data={'start_queue': True},
            token=self.user_1.auth.token,
        )
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(self.lobby1.queue)
        queue()

        t1 = Team.get_by_lobby_id(self.lobby1.id)
        self.assertIsNotNone(t1)
        self.assertTrue(t1.ready)

        # pre_match verifications
        self.assertIsNone(PreMatch.get_by_player_id(self.user_1.id))
        self.assertIsNone(PreMatch.get_by_player_id(self.user_2.id))
        self.assertIsNone(PreMatch.get_by_player_id(self.user_3.id))
        self.assertIsNone(PreMatch.get_by_player_id(self.user_4.id))

        # lobby 3 & 4 queue
        self.assertIsNone(self.lobby3.queue)
        r = self.lobby_api.call(
            'patch',
            f'/{self.lobby3.id}',
            data={'start_queue': True},
            token=self.user_3.auth.token,
        )
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(self.lobby3.queue)
        queue()

        t2 = Team.get_by_lobby_id(self.lobby3.id)
        self.assertIsNotNone(t2)
        self.assertTrue(t2.ready)

        # mm verifications
        pm1 = PreMatch.get_by_player_id(self.user_1.id)
        pm2 = PreMatch.get_by_player_id(self.user_2.id)
        pm3 = PreMatch.get_by_player_id(self.user_3.id)
        pm4 = PreMatch.get_by_player_id(self.user_4.id)
        self.assertIsNotNone(pm1)
        self.assertIsNotNone(pm2)
        self.assertIsNotNone(pm3)
        self.assertIsNotNone(pm4)
        self.assertEqual(pm1, pm2)
        self.assertEqual(pm1, pm3)
        self.assertEqual(pm1, pm4)
        self.assertEqual(pm2, pm3)
        self.assertEqual(pm2, pm4)
        self.assertEqual(pm3, pm4)
        pre_match = pm1
        self.assertEqual(self.user_1.account.pre_match, pre_match)
        self.assertEqual(self.user_2.account.pre_match, pre_match)
        self.assertEqual(self.user_3.account.pre_match, pre_match)
        self.assertEqual(self.user_4.account.pre_match, pre_match)

        ids1 = [obj.id for obj in pre_match.teams]
        ids2 = [obj.id for obj in (t1, t2)]
        self.assertEqual(sorted(ids1), sorted(ids2))

        users = [self.user_1, self.user_2, self.user_3, self.user_4]

        # test get pre_match details
        for user in users:
            r = self.pre_match_api.call(
                'get',
                '/',
                token=user.auth.token,
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json().get('id'), pre_match.id)
            self.assertEqual(r.json().get('status'), PreMatch.Statuses.LOCK_IN)
            queue()

        # test lockin
        for user in users[:-1]:
            r = self.pre_match_api.call(
                'post',
                '/lock-in',
                token=user.auth.token,
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json().get('id'), pre_match.id)
            self.assertEqual(r.json().get('status'), PreMatch.Statuses.LOCK_IN)
            queue()

        cancel_match_after_countdown(pre_match.id, run_once=True)
        self.assertIsNotNone(PreMatch.get_by_id(pre_match.id))

        t1 = Team.get_by_lobby_id(self.lobby1.id)
        self.assertIsNotNone(t1)
        self.assertTrue(t1.ready)

        t2 = Team.get_by_lobby_id(self.lobby3.id)
        self.assertIsNotNone(t2)
        self.assertTrue(t2.ready)

        ids1 = [obj.id for obj in pre_match.teams]
        ids2 = [obj.id for obj in (t1, t2)]
        self.assertEqual(sorted(ids1), sorted(ids2))

        r = self.pre_match_api.call(
            'post',
            '/lock-in',
            token=self.user_4.auth.token,
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get('id'), pre_match.id)
        self.assertEqual(r.json().get('status'), PreMatch.Statuses.READY_IN)
        self.assertEqual(r.json().get('countdown'), settings.MATCH_READY_COUNTDOWN)

        queue()
        cancel_match_after_countdown(pre_match.id, run_once=True)
        self.assertIsNotNone(PreMatch.get_by_id(pre_match.id))

        time.sleep(1)
        self.assertTrue(pre_match.countdown < settings.MATCH_READY_COUNTDOWN)

        for user in users[:-1]:
            r = self.pre_match_api.call(
                'post',
                '/ready',
                token=user.auth.token,
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.json().get('id'), pre_match.id)
            self.assertEqual(r.json().get('status'), PreMatch.Statuses.READY_IN)

            queue()
            cancel_match_after_countdown(pre_match.id, run_once=True)
            self.assertIsNotNone(PreMatch.get_by_id(pre_match.id))

        self.assertEqual(Match.objects.all().count(), 0)
        baker.make(Server)

        r = self.pre_match_api.call(
            'post',
            '/ready',
            token=self.user_4.auth.token,
        )
        self.assertEqual(r.status_code, 201)
        queue()
        cancel_match_after_countdown(pre_match.id, run_once=True)
        match = Match.objects.first()
        self.assertEqual(r.json().get('id'), match.id)
        with self.assertRaises(PreMatchException):
            PreMatch.get_by_id(pre_match.id)

        self.assertEqual(match.status, Match.Status.WARMUP)
