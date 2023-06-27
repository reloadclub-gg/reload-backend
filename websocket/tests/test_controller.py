from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from model_bakery import baker

from accounts.api.schemas import FriendAccountSchema, UserSchema
from accounts.models import Account
from accounts.tests.mixins import UserWithFriendsMixin
from core.tests import TestCase
from lobbies.api.schemas import LobbyInviteSchema, LobbySchema
from lobbies.models import Lobby
from matches.api.schemas import MatchSchema
from matches.models import Match, Server
from notifications.api.schemas import NotificationSchema
from notifications.models import Notification
from pre_matches.api.schemas import PreMatchSchema
from pre_matches.models import PreMatch
from pre_matches.tests.mixins import TeamsMixin
from steam import Steam
from websocket import controller

User = get_user_model()


class WSControllerTestCase(UserWithFriendsMixin, TestCase):
    def __get_online_friends(self):
        steam_friends_ids = [
            friend.get('steamid')
            for friend in Steam.get_player_friends(self.user.steam_user)
        ]

        friends = [
            account
            for account in Account.objects.filter(
                user__is_active=True,
                is_verified=True,
                user__is_staff=False,
                steamid__in=steam_friends_ids,
            ).exclude(user_id=self.user.id)
        ]
        return [friend for friend in friends if friend.user.is_online]

    def __create_lobbies(self):
        self.user.auth.add_session()
        self.friend1.auth.add_session()
        self.friend2.auth.add_session()
        return [
            Lobby.create(self.user.id),
            Lobby.create(self.friend1.id),
            Lobby.create(self.friend2.id),
        ]

    def __lobby_invites(self):
        self.user.auth.add_session()
        self.friend1.auth.add_session()
        self.friend2.auth.add_session()

        lobby1 = Lobby.create(self.user.id)
        lobby2 = Lobby.create(self.friend1.id)
        lobby3 = Lobby.create(self.friend2.id)

        return [
            lobby1.invite(self.user.id, self.friend1.id),
            lobby2.invite(self.friend1.id, self.friend2.id),
            lobby3.invite(self.friend2.id, self.user.id),
        ]

    def __get_schema_dict(self, schema, obj):
        return schema.from_orm(obj).dict()

    async def test_user_update(self):
        data = await sync_to_async(controller.user_update)(self.user)
        expected_payload = await sync_to_async(self.__get_schema_dict)(
            UserSchema, self.user
        )

        self.assertEqual(data.get('payload'), expected_payload)
        self.assertEqual(data.get('meta').get('action'), 'ws_userUpdate')

    async def test_user_status_change(self):
        data = await sync_to_async(controller.user_status_change)(self.user)

        expected_payload = await sync_to_async(self.__get_schema_dict)(
            FriendAccountSchema, self.user.account
        )

        self.assertEqual(data.get('payload'), expected_payload)
        self.assertEqual(data.get('meta').get('action'), 'ws_userStatusChange')

    async def test_friendlist_add(self):
        self.friend1.auth.add_session()
        self.friend2.auth.add_session()
        friends = await sync_to_async(self.__get_online_friends)()
        online_friends_ids = [friend.user.id for friend in friends]

        data = await sync_to_async(controller.friendlist_add)(
            self.user, online_friends_ids
        )
        expected_payload = await sync_to_async(self.__get_schema_dict)(
            FriendAccountSchema, self.user.account
        )

        self.assertEqual(data.get('payload'), expected_payload)
        self.assertEqual(data.get('meta').get('action'), 'ws_friendlistAdd')

    async def test_lobby_update(self):
        lobbies = await sync_to_async(self.__create_lobbies)()
        results = await sync_to_async(controller.lobby_update)(lobbies)
        self.assertEqual(len(results), len(lobbies))
        expected_payload = await sync_to_async(self.__get_schema_dict)(
            LobbySchema, lobbies[0]
        )
        assert any(data.get('payload') == expected_payload for data in results)

    async def test_lobby_player_invite(self):
        invites = await sync_to_async(self.__lobby_invites)()
        data = await sync_to_async(controller.lobby_player_invite)(invites[0])
        expected_payload = await sync_to_async(self.__get_schema_dict)(
            LobbyInviteSchema, invites[0]
        )

        self.assertEqual(data.get('payload'), expected_payload)
        self.assertEqual(data.get('meta').get('action'), 'ws_lobbyInviteReceived')

    async def test_lobby_player_refuse_invite(self):
        invites = await sync_to_async(self.__lobby_invites)()
        data = await sync_to_async(controller.lobby_player_refuse_invite)(invites[0])
        expected_payload = await sync_to_async(self.__get_schema_dict)(
            LobbyInviteSchema, invites[0]
        )

        self.assertEqual(data.get('payload'), expected_payload)
        self.assertEqual(data.get('meta').get('action'), 'ws_refuseInvite')

    async def test_lobby_invites_update(self):
        invites = await sync_to_async(self.__lobby_invites)()
        lobby = await sync_to_async(Lobby)(owner_id=invites[0].lobby_id)

        results = await sync_to_async(controller.lobby_invites_update)(lobby)
        self.assertEqual(len(results), len(lobby.invites))
        expected_payload = await sync_to_async(self.__get_schema_dict)(
            LobbyInviteSchema, lobby.invites[0]
        )
        assert all(data.get('payload') == expected_payload for data in results)
        assert all(
            data.get('meta').get('action') == 'ws_updateInvite' for data in results
        )

        results = await sync_to_async(controller.lobby_invites_update)(lobby, True)
        assert all(data.get('payload') == expected_payload for data in results)
        assert all(
            data.get('meta').get('action') == 'ws_removeInvite' for data in results
        )

    async def test_user_lobby_invites_expire(self):
        await sync_to_async(self.__lobby_invites)()
        user_invites = (
            self.user.account.lobby_invites_sent + self.user.account.lobby_invites
        )

        results = await sync_to_async(controller.user_lobby_invites_expire)(self.user)
        self.assertEqual(len(results), len(user_invites))

        expected_payload = await sync_to_async(self.__get_schema_dict)(
            LobbyInviteSchema, user_invites[0]
        )
        assert any(data.get('payload') == expected_payload for data in results)
        assert all(
            data.get('meta').get('action') == 'ws_removeInvite' for data in results
        )


class WSControllerMatchesTestCase(TeamsMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.server = baker.make(Server)

    def __get_schema_dict(self, schema, obj):
        return schema.from_orm(obj).dict()

    def __create_match(self):
        match = baker.make(Match, server=self.server)
        team1 = match.matchteam_set.create(name=self.team1.name)
        team2 = match.matchteam_set.create(name=self.team2.name)

        return (match, team1, team2)

    def __create_pre_match(self):
        pre_match = PreMatch.create(self.team1.id, self.team2.id)
        return (pre_match, pre_match.players)

    def __create_notification(self):
        return Notification.create('notification content', 'avatar', self.user_1.id)

    async def test_pre_match(self):
        pre_match, players = await sync_to_async(self.__create_pre_match)()
        results = await sync_to_async(controller.pre_match)(pre_match)
        self.assertEqual(len(results), len(players))

        expected_payload = await sync_to_async(self.__get_schema_dict)(
            PreMatchSchema, pre_match
        )
        assert all(data.get('payload') == expected_payload for data in results)
        assert all(data.get('meta').get('action') == 'ws_preMatch' for data in results)

    async def test_match_cancel(self):
        pre_match, _ = await sync_to_async(self.__create_pre_match)()
        data = await sync_to_async(controller.match_cancel)(pre_match)

        self.assertIsNone(data.get('payload'))
        self.assertEqual(data.get('meta').get('action'), 'ws_preMatchCancel')

    async def test_match_cancel_warn(self):
        data = await sync_to_async(controller.match_cancel_warn)(
            self.user_1.account.lobby
        )

        self.assertIsNone(data.get('payload'))
        self.assertEqual(data.get('meta').get('action'), 'ws_preMatchCancelWarn')

    async def test_restart_queue(self):
        data = await sync_to_async(controller.restart_queue)(self.user_1.account.lobby)

        self.assertIsNone(data.get('payload'))
        self.assertEqual(data.get('meta').get('action'), 'ws_restartQueue')

    async def test_match(self):
        match, team1, team2 = await sync_to_async(self.__create_match)()
        data = await sync_to_async(controller.match)(match)

        expected_payload = await sync_to_async(self.__get_schema_dict)(
            MatchSchema, match
        )

        self.assertEqual(data.get('payload'), expected_payload)
        self.assertEqual(data.get('meta').get('action'), 'ws_match')

    async def test_new_notification(self):
        notification = await sync_to_async(self.__create_notification)()
        data = await sync_to_async(controller.new_notification)(notification)

        expected_payload = await sync_to_async(self.__get_schema_dict)(
            NotificationSchema, notification
        )

        self.assertEqual(data.get('payload'), expected_payload)
        self.assertEqual(data.get('meta').get('action'), 'ws_newNotification')
