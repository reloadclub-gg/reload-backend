from model_bakery import baker

from accounts.utils import calc_level_and_points, steamid64_to_hex
from core.tests import TestCase
from core.utils import get_full_file_path
from matches import models
from matches.api import schemas
from pre_matches.tests.mixins import TeamsMixin
from steam import Steam
from store.models import Item, UserItem


class MatchesSchemasTestCase(TeamsMixin, TestCase):
    def test_map_schema(self):
        map = baker.make(models.Map, id=1, name="Map name", sys_name="map_name")
        payload = schemas.MapSchema.from_orm(map).dict()
        expected_payload = {
            "id": 1,
            "name": "Map name",
            "sys_name": "map_name",
            "sys_id": map.sys_id,
            "is_active": True,
            "thumbnail": get_full_file_path(map.thumbnail) if map.thumbnail else None,
            "map_type": map.map_type,
        }

        self.assertEqual(payload, expected_payload)

    def test_match_schema(self):
        map = baker.make(models.Map, id=1, name="Map name", sys_name="map_name")
        match = baker.make(models.Match, map=map)
        baker.make(models.MatchTeam, match=match, side=1)
        baker.make(models.MatchTeam, match=match, side=2)
        payload = schemas.MatchSchema.from_orm(match).dict()

        expected_payload = {
            "id": match.id,
            "create_date": match.create_date.isoformat(),
            "start_date": match.start_date.isoformat() if match.start_date else None,
            "end_date": match.end_date.isoformat() if match.end_date else None,
            "status": match.status,
            "match_type": match.match_type,
            "game_mode": match.game_mode,
            "server_ip": match.server.ip,
            "server_port": match.server.port,
            "teams": [schemas.MatchTeamSchema.from_orm(team) for team in match.teams],
            "rounds": match.rounds,
            "winner_id": match.winner.id if match.winner else None,
            "map": schemas.MapSchema.from_orm(map),
            "restricted_weapon": match.restricted_weapon,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_player_schema(self):
        self.user_1.account.level_points = 95
        self.user_1.account.save()
        match = baker.make(models.Match, status=models.Match.Status.WARMUP)
        team = baker.make(models.MatchTeam, match=match, score=10, side=1)
        baker.make(models.MatchTeam, match=match, side=2)
        match_player = baker.make(models.MatchPlayer, team=team, user=self.user_1)
        match.start()
        match.finish()

        payload = schemas.MatchPlayerSchema.from_orm(match_player).dict()
        expected_payload = {
            "id": match_player.id,
            "user_id": match_player.user.id,
            "team_id": match_player.team.id,
            "match_id": match_player.team.match.id,
            "username": match_player.user.steam_user.username,
            "avatar": match_player.user.account.avatar_dict,
            "progress": {
                "points_earned": match_player.points_earned,
                "level_before": match_player.level,
                "level_after": calc_level_and_points(
                    match_player.points_earned,
                    match_player.level,
                    match_player.level_points,
                )[0],
                "level_points_before": match_player.level_points,
                "level_points_after": calc_level_and_points(
                    match_player.points_earned,
                    match_player.level,
                    match_player.level_points,
                )[1],
            },
            "stats": schemas.MatchPlayerStatsSchema.from_orm(match_player.stats).dict(),
            "level": match_player.user.account.level,
            "status": match_player.user.status,
            "steam_url": match_player.user.steam_user.profileurl,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_with_players_schema(self):
        map = baker.make(models.Map, id=1, name="Map name", sys_name="map_name")
        match = baker.make(models.Match, map=map)
        team_a = match.matchteam_set.create(name="Team A", side=1)
        team_b = match.matchteam_set.create(name="Team B", side=2)
        baker.make(models.MatchPlayer, user=self.user_1, team=team_a)
        baker.make(models.MatchPlayer, user=self.user_2, team=team_a)
        baker.make(models.MatchPlayer, user=self.user_3, team=team_a)
        baker.make(models.MatchPlayer, user=self.user_4, team=team_a)
        baker.make(models.MatchPlayer, user=self.user_5, team=team_a)
        baker.make(models.MatchPlayer, user=self.user_6, team=team_b)
        baker.make(models.MatchPlayer, user=self.user_7, team=team_b)
        baker.make(models.MatchPlayer, user=self.user_8, team=team_b)
        baker.make(models.MatchPlayer, user=self.user_9, team=team_b)
        baker.make(models.MatchPlayer, user=self.user_10, team=team_b)

        if match.status == models.Match.Status.LOADING:
            status = "loading"
        elif match.status == models.Match.Status.RUNNING:
            status = "running"
        else:
            status = "finished"

        payload = schemas.MatchSchema.from_orm(match).dict()
        expected_payload = {
            "id": match.id,
            "create_date": match.create_date.isoformat(),
            "start_date": match.start_date.isoformat() if match.start_date else None,
            "end_date": match.end_date.isoformat() if match.end_date else None,
            "status": status,
            "match_type": match.match_type,
            "game_mode": match.game_mode,
            "server_ip": match.server.ip,
            "server_port": match.server.port,
            "teams": [schemas.MatchTeamSchema.from_orm(team) for team in match.teams],
            "rounds": match.rounds,
            "winner_id": match.winner.id if match.winner else None,
            "map": schemas.MapSchema.from_orm(map),
            "restricted_weapon": match.restricted_weapon,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_team_schema(self):
        match = baker.make(models.Match)
        team = baker.make(models.MatchTeam, match=match, side=1)
        payload = schemas.MatchTeamSchema.from_orm(team).dict()
        expected_payload = {
            "id": team.id,
            "name": team.name,
            "score": team.score,
            "match_id": team.match.id,
            "side": team.side,
            "players": [
                schemas.MatchPlayerSchema.from_orm(match_player)
                for match_player in match.players
            ],
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_player_progress_schema(self):
        self.user_1.account.level_points = 95
        self.user_1.account.save()
        match = baker.make(models.Match, status=models.Match.Status.WARMUP)
        team = baker.make(models.MatchTeam, match=match, score=10, side=1)
        baker.make(models.MatchTeam, match=match, side=2)
        match_player = baker.make(models.MatchPlayer, team=team, user=self.user_1)
        match.start()
        match.finish()

        payload = schemas.MatchPlayerProgressSchema.from_orm(match_player).dict()
        expected_payload = {
            "points_earned": match_player.points_earned,
            "level_before": match_player.level,
            "level_after": calc_level_and_points(
                match_player.points_earned,
                match_player.level,
                match_player.level_points,
            )[0],
            "level_points_before": match_player.level_points,
            "level_points_after": calc_level_and_points(
                match_player.points_earned,
                match_player.level,
                match_player.level_points,
            )[1],
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_player_stats_schema(self):
        self.user_1.account.level_points = 95
        self.user_1.account.save()
        match = baker.make(models.Match, status=models.Match.Status.WARMUP)
        team = baker.make(models.MatchTeam, match=match, score=10, side=1)
        baker.make(models.MatchTeam, match=match, side=2)
        match_player = baker.make(models.MatchPlayer, team=team, user=self.user_1)
        match.start()
        match.finish()

        payload = schemas.MatchPlayerStatsSchema.from_orm(match_player.stats).dict()
        expected_payload = {
            "kills": match_player.stats.kills,
            "deaths": match_player.stats.deaths,
            "assists": match_player.stats.assists,
            "damage": match_player.stats.damage,
            "hs_kills": match_player.stats.hs_kills,
            "afk": match_player.stats.afk,
            "plants": match_player.stats.plants,
            "defuses": match_player.stats.defuses,
            "double_kills": match_player.stats.double_kills,
            "triple_kills": match_player.stats.triple_kills,
            "quadra_kills": match_player.stats.quadra_kills,
            "aces": match_player.stats.aces,
            "clutch_v1": match_player.stats.clutch_v1,
            "clutch_v2": match_player.stats.clutch_v2,
            "clutch_v3": match_player.stats.clutch_v3,
            "clutch_v4": match_player.stats.clutch_v4,
            "clutch_v5": match_player.stats.clutch_v5,
            "firstkills": match_player.stats.firstkills,
            "shots_fired": match_player.stats.shots_fired,
            "head_shots": match_player.stats.head_shots,
            "chest_shots": match_player.stats.chest_shots,
            "other_shots": match_player.stats.other_shots,
            "rounds_played": match_player.stats.rounds_played,
            "clutches": match_player.stats.clutches,
            "shots_hit": match_player.stats.shots_hit,
            "adr": match_player.stats.adr,
            "kdr": match_player.stats.kdr,
            "kda": match_player.stats.kda,
            "ahk": match_player.stats.ahk,
            "ahr": match_player.stats.ahr,
            "hsk": match_player.stats.hsk,
            "accuracy": match_player.stats.accuracy,
            "head_accuracy": match_player.stats.head_accuracy,
            "chest_accuracy": match_player.stats.chest_accuracy,
            "others_accuracy": match_player.stats.others_accuracy,
        }
        self.assertEqual(payload, expected_payload)

    def test_match_creation_schema_invalid_mode(self):
        with self.assertRaisesRegex(ValueError, "Invalid mode"):
            schemas.MatchCreationSchema.from_orm(
                {
                    "players_ids": [self.user_1.id],
                    "mode": "test",
                }
            ).dict()

    def test_match_creation_schema_invalid_players_length(self):
        with self.assertRaisesRegex(ValueError, "Invalid number of players"):
            schemas.MatchCreationSchema.from_orm(
                {"players_ids": [self.user_1.id]}
            ).dict()

    def test_match_creation_schema_invalid_map_id(self):
        with self.assertRaisesRegex(ValueError, "Invalid map"):
            schemas.MatchCreationSchema.from_orm(
                {
                    "players_ids": [self.user_1.id],
                    "mode": "custom",
                    "map_id": 4,
                }
            ).dict()

    def test_match_creation_schema_custom_without_players(self):
        map = baker.make(models.Map, id=1)
        with self.assertRaisesRegex(ValueError, "Invalid number of players"):
            schemas.MatchCreationSchema.from_orm(
                {
                    "players_ids": [self.user_1.id],
                    "mode": "custom",
                    "map_id": map.id,
                    "spec_players_ids": [self.user_1.id],
                }
            ).dict()

    def test_match_creation_schema_invalid_weapon(self):
        map = baker.make(models.Map, id=1)
        with self.assertRaisesRegex(ValueError, "Invalid weapon"):
            schemas.MatchCreationSchema.from_orm(
                {
                    "players_ids": [self.user_1.id],
                    "mode": "custom",
                    "map_id": map.id,
                    "def_players_ids": [self.user_1.id],
                    "weapon": "katana",
                }
            ).dict()

    def test_match_creation_schema_custom_invalid_players_length(self):
        map = baker.make(models.Map, id=1)
        with self.assertRaisesRegex(ValueError, "Invalid number of players"):
            schemas.MatchCreationSchema.from_orm(
                {
                    "players_ids": [self.user_1.id, self.user_2.id],
                    "mode": "custom",
                    "map_id": map.id,
                    "def_players_ids": [self.user_1.id],
                }
            ).dict()

    def test_match_creation_schema_custom(self):
        map = baker.make(models.Map, id=1)
        payload = schemas.MatchCreationSchema.from_orm(
            {
                "players_ids": [self.user_1.id, self.user_2.id, self.user_3.id],
                "mode": models.Match.GameMode.CUSTOM,
                "map_id": map.id,
                "def_players_ids": [self.user_1.id],
                "atk_players_ids": [self.user_2.id],
                "spec_players_ids": [self.user_2.id],
                "weapon": models.Match.WeaponChoices.WEAPON_HEAVYSNIPER,
            }
        ).dict()

        expected_payload = {
            "players_ids": [self.user_1.id, self.user_2.id, self.user_3.id],
            "mode": models.Match.GameMode.CUSTOM,
            "map_id": map.id,
            "def_players_ids": [self.user_1.id],
            "atk_players_ids": [self.user_2.id],
            "spec_players_ids": [self.user_2.id],
            "weapon": models.Match.WeaponChoices.WEAPON_HEAVYSNIPER,
        }
        self.assertEqual(payload, expected_payload)

    def test_match_creation_schema_comp(self):
        payload = schemas.MatchCreationSchema.from_orm(
            {
                "players_ids": [
                    self.user_1.id,
                    self.user_2.id,
                    self.user_3.id,
                    self.user_4.id,
                    self.user_5.id,
                    self.user_6.id,
                    self.user_7.id,
                    self.user_8.id,
                    self.user_9.id,
                    self.user_10.id,
                ],
            }
        ).dict()

        expected_payload = {
            "players_ids": [
                self.user_1.id,
                self.user_2.id,
                self.user_3.id,
                self.user_4.id,
                self.user_5.id,
                self.user_6.id,
                self.user_7.id,
                self.user_8.id,
                self.user_9.id,
                self.user_10.id,
            ],
            "mode": models.Match.GameMode.COMPETITIVE,
            "map_id": None,
            "def_players_ids": [],
            "atk_players_ids": [],
            "spec_players_ids": [],
            "weapon": None,
        }
        self.assertEqual(payload, expected_payload)

    def test_match_fivem_schema_comp(self):
        map = baker.make(models.Map, id=1, name="Map name", sys_name="map_name")
        match = baker.make(models.Match, map=map)
        baker.make(models.MatchTeam, match=match, side=1)
        baker.make(models.MatchTeam, match=match, side=2)
        payload = schemas.FivemMatchSchema.from_orm(match).dict()

        expected_payload = {
            "match_id": match.id,
            "game_mode": match.game_mode,
            "players": [
                schemas.FivemPlayerSchema.from_orm(player) for player in match.players
            ],
            "match_type": match.match_type,
            "map": map.sys_id,
            "restricted_weapon": match.restricted_weapon,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_match_fivem_schema_custom(self):
        map = baker.make(models.Map, id=1, name="Map name", sys_name="map_name")
        match = baker.make(
            models.Match,
            map=map,
            game_mode="custom",
        )
        team = baker.make(models.MatchTeam, match=match, side=1)
        baker.make(models.MatchTeam, match=match, side=2)
        baker.make(models.MatchPlayer, team=team, user=self.user_1)
        payload = schemas.FivemMatchSchema.from_orm(match).dict()
        expected_payload = {
            "match_id": match.id,
            "game_mode": match.game_mode,
            "players": [
                schemas.FivemPlayerSchema.from_orm(player) for player in match.players
            ],
            "match_type": match.match_type,
            "map": map.sys_id,
            "restricted_weapon": match.restricted_weapon,
        }
        self.assertDictEqual(payload, expected_payload)

    def test_player_fivem_schema(self):
        self.user_1.account.level_points = 95
        self.user_1.account.save()
        match = baker.make(models.Match, status=models.Match.Status.LOADING)
        team = baker.make(models.MatchTeam, match=match, score=10, side=1)
        baker.make(models.MatchTeam, match=match, side=2)
        match_player = baker.make(models.MatchPlayer, team=team, user=self.user_1)

        payload = schemas.FivemPlayerSchema.from_orm(match_player).dict()
        expected_payload = {
            "id": match_player.user.id,
            "username": match_player.user.account.username,
            "steamid": steamid64_to_hex(match_player.user.account.steamid),
            "steamid64": match_player.user.account.steamid,
            "team_id": team.side,
            "team_name": team.name,
            "level": match_player.level,
            "avatar": Steam.build_avatar_url(
                match_player.user.steam_user.avatarhash,
                "medium",
            ),
            "assets": {"persona": None, "spray": None, "wear": None, "weapon": None},
        }

        self.assertEqual(payload, expected_payload)

        item = baker.make(Item, item_type="spray", name="spray_1")
        UserItem.objects.create(item=item, user=self.user_1, in_use=True)
        payload = schemas.FivemPlayerSchema.from_orm(match_player).dict()
        expected_payload = {
            "id": match_player.user.id,
            "username": match_player.user.account.username,
            "steamid": steamid64_to_hex(match_player.user.account.steamid),
            "steamid64": match_player.user.account.steamid,
            "level": match_player.user.account.level,
            "avatar": Steam.build_avatar_url(
                match_player.user.steam_user.avatarhash,
                "medium",
            ),
            "assets": {
                "persona": None,
                "spray": item.handle,
                "wear": None,
                "weapon": None,
            },
            "team_id": team.side,
            "team_name": team.name,
        }

        self.assertEqual(payload, expected_payload)
