from datetime import datetime
from unittest import mock

from ninja.errors import AuthenticationError, Http404, HttpError

from core.tests import TestCase
from matches.models import Match

from ..api import controller
from ..models import Lobby, LobbyInvite, PreMatch, PreMatchConfig, Team
from . import mixins


class LobbyControllerTestCase(mixins.VerifiedPlayersMixin, TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()

    def test_lobby_remove_player(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

        controller.lobby_remove_player(self.user_2.id, lobby_1.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_remove_player_from_wrong_lobby(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

        with self.assertRaises(HttpError):
            controller.lobby_remove_player(self.user_2.id, lobby_2.id)

    def test_lobby_invite(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        controller.lobby_invite(
            lobby_id=lobby_1.id,
            from_user_id=self.user_1.id,
            to_user_id=self.user_2.id,
        )

        self.assertEqual(
            lobby_1.invites,
            [
                LobbyInvite(
                    lobby_id=lobby_1.id, from_id=self.user_1.id, to_id=self.user_2.id
                )
            ],
        )

    def test_lobby_accept_invite(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        invite = lobby_2.invite(lobby_2.id, lobby_1.id)

        controller.lobby_accept_invite(self.user_1, lobby_2.id, invite.id)

        self.assertListEqual(lobby_2.invites, [])
        self.assertEqual(lobby_2.players_count, 2)

    @mock.patch('matchmaking.api.controller.lobby_move')
    def test_lobby_accept_invite_mocked(self, mock_move):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        invite = lobby_2.invite(lobby_2.id, lobby_1.id)

        controller.lobby_accept_invite(self.user_1, lobby_2.id, invite.id)

        mock_move.assert_called_once()

    def test_lobby_refuse_invite(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_2.invite(lobby_2.id, lobby_1.id)

        self.assertListEqual(
            lobby_2.invites,
            [
                LobbyInvite(
                    lobby_id=lobby_2.id, from_id=self.user_2.id, to_id=self.user_1.id
                )
            ],
        )
        self.assertEqual(lobby_1.players_count, 1)

        controller.lobby_refuse_invite(
            lobby_id=lobby_2.id, invite_id=f'{self.user_2.id}:{self.user_1.id}'
        )

        self.assertListEqual(lobby_1.invites, [])
        self.assertEqual(lobby_1.players_count, 1)

    def test_lobby_refuse_invite_with_raise(self):
        lobby = Lobby.create(self.user_1.id)

        with self.assertRaises(HttpError):
            controller.lobby_refuse_invite(lobby_id=lobby.id, invite_id='99:99')

    def test_lobby_change_type_and_mode(self):
        lobby = Lobby.create(self.user_1.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        controller.lobby_change_type_and_mode(lobby.id, 'custom', 20)

        self.assertEqual(lobby.mode, 20)
        self.assertEqual(lobby.lobby_type, 'custom')

    @mock.patch(
        'matchmaking.models.Lobby.queue',
        return_value=datetime.now(),
    )
    def test_lobby_change_type_and_mode_with_set_type_exception(self, _mock):
        lobby = Lobby.create(self.user_1.id)

        self.assertEqual(lobby.mode, 5)
        self.assertEqual(lobby.lobby_type, 'competitive')

        with self.assertRaises(HttpError):
            controller.lobby_change_type_and_mode(lobby.id, 'custom', 20)

    def test_lobby_enter(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_1.set_public()
        lobby_2 = Lobby.create(self.user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        controller.lobby_enter(self.user_2, lobby_1.id)

        self.assertEqual(lobby_1.players_count, 2)
        self.assertEqual(lobby_2.players_count, 0)

    def test_lobby_enter_isnt_public(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

        with self.assertRaises(HttpError):
            controller.lobby_enter(self.user_2, lobby_1.id)

    def test_set_public(self):
        lobby = Lobby.create(self.user_1.id)
        lobby_returned = controller.set_public(lobby.id)

        self.assertEqual(lobby_returned, lobby)
        self.assertTrue(lobby.is_public)

    def test_set_private(self):
        lobby = Lobby.create(self.user_1.id)
        lobby_returned = controller.set_private(lobby.id)

        self.assertEqual(lobby_returned, lobby)
        self.assertFalse(lobby.is_public)

    def test_lobby_leave(self):
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_2.invite(self.user_2.id, self.user_1.id)

        Lobby.move(self.user_1.id, lobby_2.id)

        self.assertEqual(lobby_1.players_count, 0)
        self.assertEqual(lobby_2.players_count, 2)

        controller.lobby_leave(self.user_1)

        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 1)

    def test_leave_lobby_full(self):
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        lobby_1 = Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)
        lobby_1.set_public()
        Lobby.move(self.user_2.id, lobby_1.id)
        Lobby.move(self.user_3.id, lobby_1.id)
        Lobby.move(self.user_4.id, lobby_1.id)
        Lobby.move(self.user_5.id, lobby_1.id)

        controller.lobby_leave(self.user_1)
        self.assertEqual(lobby_1.players_count, 1)
        self.assertEqual(lobby_2.players_count, 4)

    @mock.patch('matchmaking.api.controller.user_status_change_task.delay')
    def test_lobby_move(self, mock_status_change):
        Lobby.create(self.user_1.id)
        lobby_2 = Lobby.create(self.user_2.id)
        lobby_2.invite(self.user_2.id, self.user_1.id)

        controller.lobby_move(self.user_1, lobby_2.id)
        self.assertEqual(mock_status_change.call_count, 2)

    @mock.patch('matchmaking.api.controller.user_status_change_task.delay')
    def test_lobby_move_derived(self, mock_status_change):
        self.user_3.auth.add_session()

        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.set_public()
        Lobby.move(self.user_2.id, lobby_1.id)

        lobby_3 = Lobby.create(self.user_3.id)
        lobby_3.invite(self.user_3.id, self.user_1.id)
        controller.lobby_move(self.user_1, lobby_3.id)
        self.assertEqual(mock_status_change.call_count, 2)

    def test_lobby_start_queue(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertFalse(lobby.queue)

        controller.lobby_start_queue(lobby.id)

        self.assertTrue(lobby.queue)

    def test_lobby_start_queue_with_queued(self):
        lobby = Lobby.create(self.user_1.id)
        self.assertFalse(lobby.queue)
        lobby.start_queue()

        with self.assertRaises(HttpError):
            controller.lobby_start_queue(lobby.id)

    def test_lobby_start_queue_and_find(self):
        self.assertEqual(Team.get_all(), [])
        lobby = Lobby.create(self.user_1.id)
        controller.lobby_start_queue(lobby.id)

        team = Team.get_by_lobby_id(lobby.id, fail_silently=True)
        self.assertIsNone(team)

        lobby2 = Lobby.create(self.user_2.id)
        controller.lobby_start_queue(lobby2.id)
        team = Team.get_by_lobby_id(lobby2.id)
        self.assertIsNotNone(team)

    @mock.patch('matchmaking.api.controller.pre_match_task.delay')
    def test_lobby_start_queue_and_find_match(self, mocker):
        self.user_1.auth.add_session()
        self.user_2.auth.add_session()
        self.user_3.auth.add_session()
        self.user_4.auth.add_session()
        self.user_5.auth.add_session()
        self.user_6.auth.add_session()
        self.user_7.auth.add_session()
        self.user_8.auth.add_session()
        self.user_9.auth.add_session()
        self.user_10.auth.add_session()
        Lobby.create(self.user_2.id)
        Lobby.create(self.user_3.id)
        Lobby.create(self.user_4.id)
        Lobby.create(self.user_5.id)
        Lobby.create(self.user_7.id)
        Lobby.create(self.user_8.id)
        Lobby.create(self.user_9.id)
        Lobby.create(self.user_10.id)

        lobby1 = Lobby.create(self.user_1.id)
        lobby2 = Lobby.create(self.user_6.id)
        lobby1.set_public()
        lobby2.set_public()
        Lobby.move(self.user_2.id, lobby1.id)
        Lobby.move(self.user_3.id, lobby1.id)
        Lobby.move(self.user_4.id, lobby1.id)
        Lobby.move(self.user_5.id, lobby1.id)
        Lobby.move(self.user_7.id, lobby2.id)
        Lobby.move(self.user_8.id, lobby2.id)
        Lobby.move(self.user_9.id, lobby2.id)
        Lobby.move(self.user_10.id, lobby2.id)

        controller.lobby_start_queue(lobby1.id)
        controller.lobby_start_queue(lobby2.id)
        team1 = Team.get_by_lobby_id(lobby1.id)
        team2 = Team.get_by_lobby_id(lobby2.id)
        match = PreMatch.get_by_team_id(team1.id)
        self.assertTrue(team1 in match.teams)
        self.assertTrue(team2 in match.teams)

        mocker.assert_called_once()
        mocker.assert_called_with(match.id)

    def test_queueing_should_delete_all_invites(self):
        lobby_1 = Lobby.create(self.user_1.id)
        Lobby.create(self.user_2.id)
        lobby_1.invite(self.user_1.id, self.user_2.id)
        Lobby.move(self.user_2.id, lobby_1.id)
        self.user_3.auth.add_session()
        lobby_1.invite(self.user_2.id, self.user_3.id)

        self.assertEqual(
            lobby_1.get_invites_by_from_player_id(self.user_2.id),
            [
                LobbyInvite(
                    from_id=self.user_2.id,
                    to_id=self.user_3.id,
                    lobby_id=lobby_1.id,
                )
            ],
        )

        controller.lobby_start_queue(lobby_1.id)

        self.assertEqual(
            lobby_1.get_invites_by_from_player_id(self.user_2.id),
            [],
        )

    def test_lobby_cancel_queue(self):
        lobby = Lobby.create(self.user_1.id)
        lobby.start_queue()
        self.assertTrue(lobby.queue)

        controller.lobby_cancel_queue(lobby.id)

        self.assertFalse(lobby.queue)

    def test_lobby_cancel_queue_team(self):
        # don't create the team yet beacuse it only has one lobby
        lobby = Lobby.create(self.user_1.id)
        controller.lobby_start_queue(lobby.id)

        # creates the team by adding all queued lobbies => lobby2 and lobby1
        lobby2 = Lobby.create(self.user_2.id)
        controller.lobby_start_queue(lobby2.id)

        # do not create a new team, but add this lobby into the existent team instead
        # because it has the seats available and match all other requirements
        self.user_3.auth.add_session()
        lobby3 = Lobby.create(self.user_3.id)
        controller.lobby_start_queue(lobby3.id)

        team = Team.get_by_lobby_id(lobby2.id)
        self.assertEqual(team.players_count, 3)
        self.assertCountEqual(team.lobbies_ids, [lobby.id, lobby2.id, lobby3.id])

        # just remove the lobby that have canceled the queue
        controller.lobby_cancel_queue(lobby2.id)
        self.assertCountEqual(team.lobbies_ids, [lobby.id, lobby3.id])

        # if all lobbies cancel the queue and there's only one lobby left
        # on team, that team will be deleted
        #
        # the next time a lobby starts
        # a new queue, it will trigger a new team creation and will put
        # all the queued lobbies together again.
        controller.lobby_cancel_queue(lobby.id)
        self.assertCountEqual(team.lobbies_ids, [])


class MatchControllerTestCase(mixins.TeamsMixin, TestCase):
    def test_match_player_lock_in(self):
        match = PreMatch.create(self.team1.id, self.team2.id)
        self.assertEqual(match.players_in, 0)

        controller.match_player_lock_in(self.user_1, match.id)
        self.assertEqual(match.players_in, 1)

        with self.assertRaises(Http404):
            controller.match_player_lock_in(self.user_1, 'UNKNOWN_ID')

        with self.assertRaises(AuthenticationError):
            controller.match_player_lock_in(self.user_15, match.id)

        for _ in range(0, 8):
            match.set_player_lock_in()

        self.assertEqual(match.state, PreMatchConfig.STATES.get('pre_start'))
        controller.match_player_lock_in(self.user_10, match.id)
        self.assertEqual(match.state, PreMatchConfig.STATES.get('lock_in'))

    @mock.patch('matchmaking.api.controller.pre_match_task.delay')
    def test_match_player_ready(self, mocker):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)

        for _ in range(0, 10):
            pre_match.set_player_lock_in()

        pre_match.start_players_ready_countdown()
        controller.match_player_ready(self.user_1, pre_match.id)
        self.assertEqual(len(pre_match.players_ready), 1)

        with self.assertRaises(Http404):
            controller.match_player_ready(self.user_1, 'UNKNOWN_ID')

        with self.assertRaises(AuthenticationError):
            controller.match_player_ready(self.user_15, pre_match.id)

        for player in pre_match.players[1:9]:
            controller.match_player_ready(player, pre_match.id)

        with self.assertRaises(HttpError):
            controller.match_player_ready(self.user_1, pre_match.id)

        self.assertEqual(pre_match.state, PreMatchConfig.STATES.get('lock_in'))
        controller.match_player_ready(self.user_10, pre_match.id)
        self.assertEqual(pre_match.state, PreMatchConfig.STATES.get('ready'))
        self.assertEqual(mocker.call_count, 10)
        mocker.assert_called_with(pre_match.id)

    def test_create_match(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        for _ in range(0, 10):
            pre_match.set_player_lock_in()

        pre_match.start_players_ready_countdown()

        for player in pre_match.players[:10]:
            pre_match.set_player_ready(player.id)

        controller.create_match(pre_match)
        match_player_user1 = self.user_1.matches_set.first()
        match_player_user6 = self.user_6.matches_set.first()
        self.assertIsNotNone(match_player_user1)
        self.assertIsNotNone(match_player_user6)
        self.assertEqual(match_player_user1.match, match_player_user6.match)
        self.assertEqual(match_player_user1.team, Match.Teams.TEAM_A)
        self.assertEqual(match_player_user6.team, Match.Teams.TEAM_B)
