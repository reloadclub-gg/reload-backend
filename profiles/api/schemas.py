from collections import Counter
from functools import reduce
from typing import List

from django.contrib.auth import get_user_model
from ninja import ModelSchema

from accounts.models import Account
from matches.api.schemas import MatchPlayerStatsSchema
from matches.models import Match, MatchPlayerStats

User = get_user_model()


class ProfileSchema(ModelSchema):
    user_id: int
    username: str
    avatar: dict
    matches_played: int
    matches_won: int
    highest_win_streak: int
    latest_matches_results: List[str]
    most_kills_in_a_match: int = None
    most_damage_in_a_match: int = None
    stats: dict
    date_joined: str
    status: str

    class Config:
        model = Account
        model_exclude = [
            'id',
            'user',
            'verification_token',
            'is_verified',
            'steamid',
        ]

    @staticmethod
    def resolve_user_id(obj):
        return obj.user.id

    @staticmethod
    def resolve_username(obj):
        return obj.user.steam_user.username

    @staticmethod
    def resolve_avatar(obj):
        return obj.avatar_dict

    @staticmethod
    def resolve_matches_played(obj):
        return obj.get_matches_played_count()

    @staticmethod
    def resolve_latest_matches_results(obj):
        return obj.get_latest_matches_results()

    @staticmethod
    def resolve_stats(obj):
        match_players_stats = [
            MatchPlayerStatsSchema.from_orm(stat).dict()
            for stat in MatchPlayerStats.objects.filter(
                player__user__id=obj.user.id,
                player__team__match__status=Match.Status.FINISHED,
            )
        ]

        return dict(
            reduce(
                lambda a, b: a.update(b) or a,
                match_players_stats,
                Counter(),
            )
        )

    @staticmethod
    def resolve_most_kills_in_a_match(obj):
        return obj.get_most_stat_in_match('kills')

    @staticmethod
    def resolve_most_damage_in_a_match(obj):
        return obj.get_most_stat_in_match('damage')

    @staticmethod
    def resolve_date_joined(obj):
        return obj.user.date_joined.isoformat()

    @staticmethod
    def resolve_social_handles(obj):
        handles = {'steam': obj.steamid}
        handles.update(
            {key: value for key, value in obj.social_handles.items() if value}
        )
        return handles

    @staticmethod
    def resolve_status(obj):
        return obj.user.status


class ProfileUpdateSchema(ModelSchema):
    class Config:
        model = Account
        model_fields = ['social_handles']
