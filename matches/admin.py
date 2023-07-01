from django.contrib import admin

from . import models


@admin.register(models.Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = (
        'ip',
        'name',
        'key',
    )
    ordering = (
        'ip',
        'name',
    )


@admin.register(models.Map)
class MapAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'sys_name', 'is_active')
    list_filter = ('is_active',)


@admin.register(models.Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'server',
        'create_date',
        'start_date',
        'end_date',
        'status',
        'game_type',
        'game_mode',
        'score',
    )
    ordering = ('create_date', 'start_date', 'end_date')
    list_filter = (
        'status',
        'game_type',
        'game_mode',
    )

    def score(self, obj):
        if obj.team_a and obj.team_b:
            return f'{obj.team_a.name} {obj.team_a.score} x {obj.team_b.score} {obj.team_b.name}'

        return '- 0 x 0 -'


@admin.register(models.MatchTeam)
class MatchTeamAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'match',
        'score',
    )
    ordering = ('name',)


@admin.register(models.MatchPlayer)
class MatchPlayerAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'team',
        'match',
        'points_base',
        'points_cap',
        'points_penalties',
        'points_earned',
        'level',
        'level_points',
    )
    search_fields = ('user__email', 'user__steam_user__username', 'team__name')

    def match(self, obj):
        return obj.team.match

    def points_base(self, obj):
        return obj.points_base

    def points_cap(self, obj):
        return obj.points_cap

    def points_penalties(self, obj):
        return obj.points_penalties

    def points_earned(self, obj):
        return obj.points_earned


@admin.register(models.MatchPlayerStats)
class MatchPlayerStatsAdmin(admin.ModelAdmin):
    list_display = (
        'player',
        'match',
        'kills',
        'deaths',
        'assists',
        'afk',
    )
    search_fields = (
        'player__user__email',
        'player__user__steam_user__username',
        'player__team__name',
    )

    def match(self, obj):
        return obj.player.team.match

    def points_earned(self, obj):
        return obj.points_earned
