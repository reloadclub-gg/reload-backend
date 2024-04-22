from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from model_bakery import baker
from social_django.models import UserSocialAuth

from core.tests import TestCase, cache
from lobbies.models import Lobby
from matches.models import Map, Match, MatchPlayer, Server
from matches.tests.mixins import FinishedMatchesMixin

from .. import models, utils
from . import mixins


class AccountsAccountModelTestCase(mixins.UserOneMixin, TestCase):
    def __create_friend(self):
        user = baker.make(models.User)
        baker.make(
            UserSocialAuth,
            user=user,
            extra_data=utils.generate_steam_extra_data(),
        )
        baker.make(models.Account, user=user, is_verified=True)
        return user

    def test_account_verification_token(self):
        account = baker.make(models.Account, user=self.user)
        self.assertIsNotNone(account.verification_token)
        self.assertEqual(account.verification_token, account.DEBUG_VERIFICATION_TOKEN)

    def test_account_save(self):
        user = baker.make(models.User)
        account = models.Account(user=user)
        self.assertRaises(ValidationError, account.save)

    def test_notifications(self):
        account = baker.make(models.Account, user=self.user)
        self.assertEqual(len(account.notifications), 0)

        n = account.notify("New notification")
        self.assertEqual(len(account.notifications), 1)
        self.assertEqual(account.notifications[0].id, n.id)

    def test_highest_level(self):
        account = baker.make(models.Account, user=self.user, level_points=80)
        self.assertEqual(account.highest_level, 0)
        account.apply_points_earned(80)
        self.assertEqual(account.highest_level, 1)
        account.apply_points_earned(80)
        self.assertEqual(account.highest_level, 2)
        account.apply_points_earned(-90)
        self.assertEqual(account.highest_level, 2)
        account.apply_points_earned(-90)
        self.assertEqual(account.highest_level, 2)

    def test_apply_points_earned(self):
        account = baker.make(models.Account, user=self.user)
        points_earned = 30

        self.assertEqual(account.level_points, 0)
        account.apply_points_earned(points_earned)
        self.assertEqual(account.level_points, points_earned)


class AccountsAccountMatchModelTestCase(FinishedMatchesMixin, TestCase):

    def test_match(self):
        self.match1.status = Match.Status.LOADING
        self.match1.save()
        self.assertEqual(self.user_1.account.get_match(), self.match1)

        self.match1.status = Match.Status.RUNNING
        self.match1.save()
        self.assertEqual(self.user_1.account.get_match(), self.match1)

        self.match1.status = Match.Status.CANCELLED
        self.match1.save()
        self.assertIsNone(self.user_1.account.get_match())

        self.match1.status = Match.Status.FINISHED
        self.match1.save()
        self.assertIsNone(self.user_1.account.get_match())

    def test_matches_played(self):
        self.assertEqual(self.user_1.account.get_matches_played_count(), 3)
        server = baker.make(Server)
        match = baker.make(Match, server=server, status=Match.Status.FINISHED)
        team1 = match.matchteam_set.create(name=self.team1.name, side=1)
        match.matchteam_set.create(name=self.team2.name, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.get_matches_played_count(), 4)

    def test_matches_won(self):
        self.assertEqual(self.user_1.account.matches_won, 2)

        server = baker.make(Server)
        match = baker.make(Match, server=server, status=Match.Status.FINISHED)
        team1 = match.matchteam_set.create(
            name=self.team1.name,
            score=settings.MATCH_ROUNDS_TO_WIN,
            side=1,
        )
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.matches_won, 3)

        match.status = Match.Status.RUNNING
        match.save()
        self.assertEqual(self.user_1.account.matches_won, 2)

    def test_get_latest_matches_results(self):
        server = baker.make(Server)
        # D - V - V
        results = self.user_1.account.get_latest_matches_results(amount=3)
        self.assertEqual(results.count("V"), 2)
        self.assertEqual(results.count("D"), 1)
        self.assertEqual(results.count("N/A"), 0)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        # V - D - V - V - N/A
        results = self.user_1.account.get_latest_matches_results()
        self.assertEqual(results.count("V"), 3)
        self.assertEqual(results[0], "V")

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        results = self.user_1.account.get_latest_matches_results()
        # V - V - D - V - V
        self.assertEqual(results.count("V"), 4)
        self.assertEqual(results.count("D"), 1)
        self.assertEqual(results[0], "V")
        self.assertEqual(results[1], "V")
        self.assertEqual(results[2], "D")
        self.assertEqual(results[3], "V")
        self.assertEqual(results[4], "V")

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=8, side=1)
        match.matchteam_set.create(name=self.team2.name, score=10, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        # D - V - V - D - V
        results = self.user_1.account.get_latest_matches_results()
        self.assertEqual(results.count("D"), 2)
        self.assertEqual(results.count("V"), 3)
        self.assertEqual(results[0], "D")
        self.assertEqual(results[-1], "V")

        # D - V
        results = self.user_1.account.get_latest_matches_results(2)
        self.assertEqual(results.count("V"), 1)
        self.assertEqual(results.count("D"), 1)
        self.assertEqual(results[0], "D")
        self.assertEqual(results[1], "V")
        with self.assertRaises(IndexError):
            self.assertEqual(results[2], "V")

    def test_highest_win_streak(self):
        server = baker.make(Server)
        self.assertEqual(self.user_1.account.highest_win_streak, 2)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.highest_win_streak, 2)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.highest_win_streak, 2)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=6, side=1)
        match.matchteam_set.create(name=self.team2.name, score=10, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.highest_win_streak, 2)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(
            name=self.team1.name,
            score=settings.MATCH_ROUNDS_TO_WIN,
            side=1,
        )
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.highest_win_streak, 2)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(
            name=self.team1.name,
            score=settings.MATCH_ROUNDS_TO_WIN,
            side=1,
        )
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.highest_win_streak, 2)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(
            name=self.team1.name,
            score=settings.MATCH_ROUNDS_TO_WIN,
            side=1,
        )
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.highest_win_streak, 3)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(
            name=self.team1.name,
            score=settings.MATCH_ROUNDS_TO_WIN,
            side=1,
        )
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        baker.make(MatchPlayer, team=team1, user=self.user_1)
        self.assertEqual(self.user_1.account.highest_win_streak, 4)

    def test_get_most_stat_in_match(self):
        server = baker.make(Server)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        match_player = baker.make(MatchPlayer, team=team1, user=self.user_1)
        match_player.stats.kills = 10
        match_player.stats.damage = 100
        match_player.stats.save()
        self.assertEqual(self.user_1.account.get_most_stat_in_match("kills"), 10)
        self.assertEqual(self.user_1.account.get_most_stat_in_match("damage"), 100)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        match_player = baker.make(MatchPlayer, team=team1, user=self.user_1)
        match_player.stats.kills = 5
        match_player.stats.damage = 50
        match_player.stats.save()
        self.assertEqual(self.user_1.account.get_most_stat_in_match("kills"), 10)
        self.assertEqual(self.user_1.account.get_most_stat_in_match("damage"), 100)

        match = baker.make(
            Match,
            server=server,
            status=Match.Status.FINISHED,
            end_date=timezone.now(),
        )
        team1 = match.matchteam_set.create(name=self.team1.name, score=10, side=1)
        match.matchteam_set.create(name=self.team2.name, score=6, side=2)
        match_player = baker.make(MatchPlayer, team=team1, user=self.user_1)
        match_player.stats.kills = 15
        match_player.stats.damage = 150
        match_player.stats.save()
        self.assertEqual(self.user_1.account.get_most_stat_in_match("kills"), 15)
        self.assertEqual(self.user_1.account.get_most_stat_in_match("damage"), 150)


class AccountsInviteModelTestCase(mixins.AccountOneMixin, TestCase):
    def test_invite_create_limit_reached(self):
        baker.make(
            models.Invite,
            owned_by=self.account,
            _quantity=models.Invite.MAX_INVITES_PER_ACCOUNT,
        )

        invite = models.Invite(email="extra@email.com", owned_by=self.account)
        self.assertRaises(ValidationError, invite.clean)

        self.user.is_staff = True
        self.user.save()
        invite = models.Invite(email="extra@email.com", owned_by=self.account)
        invite.clean()

    def test_invite_create_existing_email(self):
        invite = models.Invite(email=self.user.email, owned_by=self.account)
        self.assertRaises(ValidationError, invite.clean)

    def test_invite_update(self):
        invite = baker.make(models.Invite, owned_by=self.account)
        self.assertIsNone(invite.datetime_accepted)
        invite.datetime_accepted = timezone.now()
        invite.save()

        invite.email = "other@email.com"
        self.assertRaises(ValidationError, invite.clean)


class AccountsUserModelTestCase(mixins.VerifiedAccountMixin, TestCase):
    def test_user_steam_user(self):
        user = baker.make(models.User)
        self.assertIsNone(user.steam_user)
        self.assertIsNotNone(self.user.steam_user)

    def test_user_auth(self):
        self.assertIsNotNone(self.user.auth)
        self.user.add_session()
        self.assertEqual(self.user.auth.sessions, 1)

    def test_is_online(self):
        self.assertFalse(self.user.is_online)
        self.user.add_session()
        self.assertTrue(self.user.is_online)
        self.user.auth.remove_session()
        self.assertTrue(self.user.is_online)

    def test_user_status(self):
        self.assertFalse(self.user.is_online)
        self.user.add_session()
        self.assertTrue(self.user.is_online)
        lobby = Lobby.create(self.user.id)
        lobby.set_public()

        user2 = baker.make(models.User)
        baker.make(
            UserSocialAuth,
            user=user2,
            extra_data=utils.generate_steam_extra_data(),
        )
        baker.make(models.Account, user=user2, is_verified=True)
        user2.add_session()
        Lobby.create(user2.id)
        Lobby.move(user2.id, lobby.id)

        user2.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.TEAMING)
        self.assertEqual(user2.status, models.User.Status.TEAMING)

        Lobby.move(user2.id, user2.id)

        user2.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.ONLINE)
        self.assertEqual(user2.status, models.User.Status.ONLINE)

        user3 = baker.make(models.User)
        baker.make(
            UserSocialAuth,
            user=user3,
            extra_data=utils.generate_steam_extra_data(),
        )
        baker.make(models.Account, user=user3, is_verified=True)
        user3.add_session()
        Lobby.create(user3.id)
        Lobby.move(user2.id, lobby.id)
        Lobby.move(user3.id, lobby.id)

        user2.refresh_from_db()
        user3.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.TEAMING)
        self.assertEqual(user2.status, models.User.Status.TEAMING)
        self.assertEqual(user3.status, models.User.Status.TEAMING)

        Lobby.move(user3.id, user3.id)

        user2.refresh_from_db()
        user3.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.TEAMING)
        self.assertEqual(user2.status, models.User.Status.TEAMING)
        self.assertEqual(user3.status, models.User.Status.ONLINE)

        server = baker.make(Server)
        match_map = baker.make(Map, map_type=Map.MapTypeChoices.DEFAULT)
        match = Match.objects.create(server=server, map=match_map)
        team_a = match.matchteam_set.create(name="team_a", side=1)
        team_b = match.matchteam_set.create(name="team_b", side=2)

        MatchPlayer.objects.create(user=self.user, team=team_a, match=match)
        MatchPlayer.objects.create(user=user2, team=team_b, match=match)

        user2.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.IN_GAME)
        self.assertEqual(user2.status, models.User.Status.IN_GAME)

        match.cancel()
        user2.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.ONLINE)
        self.assertEqual(user2.status, models.User.Status.ONLINE)

        server = baker.make(Server)
        match_map = baker.make(Map, map_type=Map.MapTypeChoices.DEFAULT)
        match = Match.objects.create(server=server, map=match_map)
        team_a = match.matchteam_set.create(name="team_a", side=1)
        team_b = match.matchteam_set.create(name="team_b", side=2)

        MatchPlayer.objects.create(user=self.user, team=team_a, match=match)
        MatchPlayer.objects.create(user=user2, team=team_b, match=match)

        match.warmup()
        user2.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.IN_GAME)
        self.assertEqual(user2.status, models.User.Status.IN_GAME)

        match.start()
        user2.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.IN_GAME)
        self.assertEqual(user2.status, models.User.Status.IN_GAME)

        match.finish()
        user2.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.status, models.User.Status.ONLINE)
        self.assertEqual(user2.status, models.User.Status.ONLINE)

    def test_inactivate(self):
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.date_inactivation)
        self.user.inactivate()
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.date_inactivation)

    def test_online_users(self):
        self.assertEqual(len(models.User.online_users()), 0)
        self.user.add_session()
        self.assertEqual(len(models.User.online_users()), 1)


class AccountsAuthModelTestCase(mixins.AccountOneMixin, TestCase):
    def test_token_init(self):
        auth = models.Auth(user_id=self.user.id)
        auth.create_token()
        self.assertIsNotNone(cache.get(auth.token_cache_key))

    def test_token_create(self):
        auth = models.Auth(user_id=self.user.id)
        self.assertIsNone(cache.get(auth.token_cache_key))
        auth.create_token()
        self.assertIsNotNone(cache.get(auth.token_cache_key))

    def test_token_auto_create(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        self.assertIsNotNone(cache.get(auth.token_cache_key))

    def test_token_load(self):
        created = models.Auth(user_id=self.user.id, force_token_create=True)
        loaded = models.Auth.load(created.token)
        self.assertEqual(loaded.token, created.token)

    def test_sessions(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        self.assertIsNone(auth.sessions)

    def test_sessions_add(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        auth.add_session()
        self.assertEqual(auth.sessions, 1)

    def test_sessions_remove(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        auth.add_session()
        auth.add_session()
        auth.remove_session()
        self.assertEqual(auth.sessions, 1)

    def test_sessions_set_expire(self):
        auth = models.Auth(user_id=self.user.id, force_token_create=True)
        auth.add_session()
        auth.expire_session()
        self.assertEqual(auth.sessions_ttl, models.Auth.Config.SESSION_GAP_TTL)


class AccountsUserBanTestCase(mixins.VerifiedAccountsMixin, TestCase):
    @mock.patch("accounts.signals.websocket.ws_update_user")
    @mock.patch("accounts.signals.websocket.ws_update_status_on_friendlist")
    def test_user_ban(self, mock_ws_friendlist, mock_ws_user):
        self.assertTrue(self.user_1.is_active)
        self.assertIsNone(self.user_1.date_inactivation)
        self.assertIsNone(self.user_1.reason_inactivated)

        ban = models.UserBan.objects.create(
            user=self.user_1,
            agent=self.staff_user,
            datetime_end=timezone.now() + timedelta(days=9999),
            subject=models.UserBan.Subject.CHEATING,
            description="was cheating",
        )

        self.assertFalse(self.user_1.is_active)
        self.assertIsNotNone(self.user_1.date_inactivation)
        self.assertIsNotNone(self.user_1.reason_inactivated)
        self.assertEqual(
            self.user_1.reason_inactivated,
            models.User.InactivationReason.USER_BAN,
        )

        ban.is_revoked = True
        ban.revoke_agent = self.staff_user
        ban.revoke_subject = models.UserBan.RevokeSubject.LAST_CHANCE
        ban.save()

        self.assertTrue(self.user_1.is_active)
        self.assertIsNone(self.user_1.date_inactivation)
        self.assertIsNone(self.user_1.reason_inactivated)

        self.assertEqual(mock_ws_user.call_count, 2)
        self.assertEqual(mock_ws_friendlist.call_count, 2)
