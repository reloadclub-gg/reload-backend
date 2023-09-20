import json

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from accounts.models import Account
from accounts.utils import hex_to_steamid64
from core.admin_mixins import ReadOnlyModelAdminMixin, SuperUserOnlyAdminMixin

from . import models


@admin.register(models.Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('ip', 'name', 'running_matches', 'port', 'api_port')
    ordering = (
        'ip',
        'name',
    )

    def running_matches(self, obj):
        return obj.match_set.filter(
            status__in=[
                models.Match.Status.RUNNING,
                models.Match.Status.LOADING,
            ]
        ).count()


@admin.register(models.Map)
class MapAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'id', 'sys_name', 'is_active')
    list_filter = ('is_active',)


class MatchPlayerInline(admin.TabularInline):
    model = models.MatchPlayer
    readonly_fields = ['user', 'level', 'level_points']
    extra = 0

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


class MatchTeamAdminInline(admin.TabularInline):
    model = models.MatchTeam
    readonly_fields = ['name', 'score', 'players']
    extra = 0

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def players(self, obj):
        # Get all related players
        players = models.MatchPlayer.objects.filter(team=obj)

        # Create a string representation with links to each player
        player_links = []
        for player in players:
            url = reverse('admin:accounts_user_change', args=[player.user.id])
            player_links.append(
                format_html('<a href="{}">{}</a>', url, player.user.account.username)
            )

        # Join all the player links with a comma and return as HTML
        return format_html(', '.join(player_links))

    players.short_description = 'Players'


@admin.register(models.Match)
class MatchAdmin(ReadOnlyModelAdminMixin, admin.ModelAdmin):
    change_form_template = 'matches/admin/match_change_form.html'
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
    exclude = ['map', 'chat']
    readonly_fields = ['score', 'map_name']
    inlines = [MatchTeamAdminInline]

    def map_name(self, obj):
        return obj.map

    def score(self, obj):
        if obj.team_a and obj.team_b:
            return f'{obj.team_a.name} {obj.team_a.score} x {obj.team_b.score} {obj.team_b.name}'

        return '- 0 x 0 -'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        match = models.Match.objects.get(pk=object_id)
        chat_data = []

        if match.chat:
            for message in match.chat:
                account = Account.objects.get(
                    steamid=hex_to_steamid64(message['steamid'])
                )
                message['user_id'] = account.user.id
                message['username'] = account.username
                chat_data.append(message)

            extra_context['chat_data'] = json.dumps(chat_data)
        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )


@admin.register(models.MatchTeam)
class MatchTeamAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'match',
        'score',
    )
    ordering = ('name',)
    inlines = [MatchPlayerInline]


@admin.register(models.MatchPlayer)
class MatchPlayerAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
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
class MatchPlayerStatsAdmin(SuperUserOnlyAdminMixin, admin.ModelAdmin):
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
