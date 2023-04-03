from django.contrib import admin

from .models import Match, MatchPlayer, MatchTeam, Server


@admin.register(Server)
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


@admin.register(Match)
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


@admin.register(MatchTeam)
class MatchTeamAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'match',
        'score',
    )
    ordering = ('name',)


@admin.register(MatchPlayer)
class MatchPlayerAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'team',
        'match',
        'kills',
        'deaths',
        'assists',
        'afk',
        'points_earned',
    )
    search_fields = ('user__email', 'user__steam_user__username', 'team__name')

    def match(self, obj):
        return obj.team.match

    def points_earned(self, obj):
        return obj.points_earned
