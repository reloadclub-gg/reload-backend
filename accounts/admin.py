from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from social_django.models import Association, Nonce, UserSocialAuth

from core import admin_mixins
from matches.models import MatchPlayer

from . import models

admin.site.unregister(Group)
if settings.ENVIRONMENT == 'production':
    admin.site.unregister(UserSocialAuth)
    admin.site.unregister(Association)
    admin.site.unregister(Nonce)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class UserLoginAdminInline(admin.TabularInline):
    model = models.UserLogin
    readonly_fields = ['timestamp', 'ip_address']
    extra = 1

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


class UserMatchesAdminInline(admin.TabularInline):
    model = MatchPlayer
    readonly_fields = [
        'match',
        'map',
        'team_name',
        'team_score',
        'server',
        'start_date',
        'end_date',
        'status',
        'game_type',
        'game_mode',
    ]
    exclude = ['team']

    def has_change_permission(self, request, obj=None):
        return False

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.model._meta.verbose_name = 'Match'
        formset.model._meta.verbose_name_plural = 'Matches'
        return formset

    def match(self, obj):
        url = reverse("admin:matches_match_change", args=[obj.team.match.id])
        return format_html('<a href="{}">{}</a>', url, obj.team.match.__str__())

    def team_name(self, obj):
        return obj.team.name

    def team_score(self, obj):
        return obj.team.score

    def map(self, obj):
        return obj.team.match.map.name

    def server(self, obj):
        return obj.team.match.server

    def start_date(self, obj):
        return obj.team.match.start_date

    def end_date(self, obj):
        return obj.team.match.end_date or '-'

    def status(self, obj):
        return obj.team.match.get_status_display()

    def game_type(self, obj):
        return obj.team.match.get_game_type_display()

    def game_mode(self, obj):
        return obj.team.match.get_game_mode_display()


class UserReportsAdminInline(admin.TabularInline):
    model = models.AccountReport
    extra = 0
    readonly_fields = [
        'subject_link',
        'reporter',
        'target',
        'report_points',
        'datetime_created',
    ]
    exclude = ['comments', 'subject']
    fk_name = 'target'

    def subject_link(self, obj):
        url = reverse(
            "admin:accounts_accountreport_change",
            args=[obj.id],
        )
        return format_html('<a href="{}">{}</a>', url, obj.get_subject_display())

    subject_link.short_description = 'Subject'


@admin.register(models.User)
class UserAdmin(admin_mixins.ReadOnlyModelAdminMixin, DjangoUserAdmin):
    fieldsets = (
        (
            _('ACCOUNT'),
            {
                'fields': (
                    'steamid',
                    'username',
                    'level',
                    'level_points',
                )
            },
        ),
        (_('IMPORTANT DATES'), {'fields': ('date_joined', 'last_login')}),
        (
            _('STATUSES'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'is_verified',
                    'is_online',
                    'groups',
                )
            },
        ),
        (_('ACTIVATION'), {'fields': ('verification_token',)}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'password1',
                    'password2',
                    'is_staff',
                    'is_superuser',
                ),
            },
        ),
    )
    list_display = (
        'email',
        'steamid',
        'date_joined',
        'last_login',
        'is_verified',
        'is_active',
        'is_online',
        'level',
        'level_points',
    )
    readonly_fields = [
        'steamid',
        'username',
        'last_login',
        'date_joined',
        'is_active',
        'is_online',
        'is_verified',
        'level',
        'level_points',
        'verification_token',
    ]
    search_fields = (
        'email',
        'date_joined',
        'account__steamid',
        'id',
        'account__username',
    )
    ordering = ('-date_joined', '-last_login', 'email', 'account__level')
    list_filter = ('is_active', 'is_staff', 'account__is_verified')
    inlines = [UserLoginAdminInline, UserMatchesAdminInline, UserReportsAdminInline]

    def is_online(self, obj):
        return obj.is_online

    def steamid(self, obj):
        return obj.steam_user.steamid

    def username(self, obj):
        return obj.steam_user.username

    def is_verified(self, obj):
        return obj.account.is_verified if obj.account else False

    def level(self, obj):
        return obj.account.level if obj.account else 0

    def level_points(self, obj):
        return obj.account.level_points if obj.account else 0

    def verification_token(self, obj):
        return obj.account.verification_token if obj.account else None

    is_online.boolean = True
    is_verified.boolean = True


@admin.register(models.Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ('owned_by', 'email', 'datetime_created', 'datetime_accepted')
    ordering = (
        '-datetime_created',
        '-datetime_accepted',
        'email',
    )
    list_filter = ('datetime_accepted',)
    readonly_fields = ['datetime_created', 'datetime_accepted']
    search_fields = ['email', 'owned_by__email']


@admin.register(models.Account)
class AccountAdmin(admin_mixins.SuperUserOnlyAdminMixin, admin.ModelAdmin):
    search_fields = ['username', 'user__email', 'steamid']
    readonly_fields = ['username']


@admin.register(models.AccountReport)
class AccountReportAdmin(admin.ModelAdmin):
    list_display = (
        'reporter',
        'target_link',
        'datetime_created',
        'subject',
        'report_points',
    )
    ordering = (
        '-datetime_created',
        'report_points',
    )
    list_filter = ('subject',)
    fields = [
        'reporter',
        'target',
        'subject',
        'report_points',
    ]
    search_fields = ['reporter__email', 'target__email']
    autocomplete_fields = ['target', 'reporter']

    def target_link(self, obj):
        url = reverse("admin:accounts_user_change", args=[obj.target.id])
        return format_html('<a href="{}">{}</a>', url, obj.target.email)

    target_link.short_description = 'Target'
