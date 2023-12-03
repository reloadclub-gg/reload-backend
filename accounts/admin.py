from copy import deepcopy

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django_object_actions import DjangoObjectActions, action
from social_django.models import Association, Nonce, UserSocialAuth

from core import admin_mixins
from matches.models import MatchPlayer
from store.models import UserBox, UserItem

from . import forms, models

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
    verbose_name = 'Match'
    verbose_name_plural = 'Matches'
    readonly_fields = [
        'match',
        'map',
        'team_name',
        'score',
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

    def score(self, obj):
        return f'{obj.team.match.team_a.score} x {obj.team.match.team_b.score}'

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
    readonly_fields = ['datetime_created']
    fk_name = 'target'

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return True


class UserItemAdminInline(admin.TabularInline):
    model = UserItem
    readonly_fields = [
        'item_type',
        'item_subtype',
        'item_is_available',
        'can_use',
        'purchase_date',
        'in_use',
    ]
    extra = 0

    def item_type(self, obj):
        return obj.item.item_type

    def item_subtype(self, obj):
        return obj.item.subtype

    def item_is_available(self, obj):
        return obj.item.is_available


class UserBoxAdminInline(admin.TabularInline):
    model = UserBox
    readonly_fields = [
        'box_is_available',
        'can_open',
        'purchase_date',
        'open_date',
    ]
    extra = 0

    def box_is_available(self, obj):
        return obj.box.is_available


class CustomUserStatusFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return models.User.Status.choices + [('available', 'Available')]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        if self.value() == models.User.Status.ONLINE:
            return queryset.filter(status__in=models.User.online_statuses)
        elif self.value() == 'available':
            return queryset.filter(status=models.User.Status.ONLINE)
        else:
            return queryset.filter(status=self.value())


class CustomUserRestrictedFilter(admin.SimpleListFilter):
    title = 'Is Restricted'
    parameter_name = 'is_restricted'

    def lookups(self, request, model_admin):
        return [('yes', 'Yes'), ('no', 'No')]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        if self.value() == 'yes':
            return queryset.filter(playerrestriction__end_date__gte=timezone.now())
        elif self.value() == 'no':
            return queryset.filter(
                Q(playerrestriction__isnull=True)
                | Q(playerrestriction__end_date__lte=timezone.now())
            )
        else:
            return queryset


@admin.register(models.User)
class UserAdmin(
    DjangoObjectActions,
    admin_mixins.CannotDeleteModelAdminMixin,
    DjangoUserAdmin,
):
    form = forms.UserUpdateForm
    add_form = forms.UserAddForm
    fieldsets = (
        (
            _('ACCOUNT'),
            {
                'fields': (
                    'steamid',
                    'username',
                    'level',
                    'level_points',
                    'highest_level',
                    'coins',
                    'date_joined',
                    'last_login',
                    'social_handles',
                )
            },
        ),
        (
            _('STATUSES'),
            {
                'fields': (
                    'is_alpha',
                    'is_beta',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'is_verified',
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
                    'steamid',
                    'username',
                    'is_staff',
                    'is_superuser',
                    'is_alpha',
                    'is_beta',
                    'groups',
                ),
            },
        ),
    )
    list_display = (
        'email',
        'steamid',
        'formatted_date_joined',
        'formatted_last_login',
        'is_alpha',
        'is_beta',
        'is_verified',
        'is_active',
        'status',
        'level',
        'level_points',
        'coins',
        'report_points',
        'restriction_countdown',
    )
    readonly_fields = [
        'last_login',
        'date_joined',
        'status',
        'is_verified',
        'verification_token',
        'social_handles',
        'highest_level',
    ]
    search_fields = (
        'email',
        'date_joined',
        'account__steamid',
        'id',
        'account__username',
    )
    ordering = ('-last_login', '-date_joined', 'email', 'account__level')
    list_filter = (
        CustomUserStatusFilter,
        'is_alpha',
        'is_beta',
        'is_active',
        'is_staff',
        'account__is_verified',
        CustomUserRestrictedFilter,
    )
    inlines = [
        UserLoginAdminInline,
        UserMatchesAdminInline,
        UserReportsAdminInline,
        UserItemAdminInline,
        UserBoxAdminInline,
    ]

    def steamid(self, obj):
        if obj.steam_user:
            return obj.steam_user.steamid

    def username(self, obj):
        if obj.steam_user:
            return obj.steam_user.username

    def is_verified(self, obj):
        return obj.account.is_verified if obj.account else False

    def level(self, obj):
        return obj.account.level if obj.account else 0

    def level_points(self, obj):
        return obj.account.level_points if obj.account else 0

    def verification_token(self, obj):
        return obj.account.verification_token if obj.account else None

    def social_handles(self, obj):
        if not obj.account or not obj.account.social_handles:
            return '-'

        return ', '.join(
            f'{k.capitalize()}: {v}' for k, v in obj.account.social_handles.items() if v
        )

    def coins(self, obj):
        return obj.account.coins if obj.account else 0

    def report_points(self, obj):
        return sum(obj.reports_received.all().values_list('report_points', flat=True))

    def highest_level(self, obj):
        return obj.account.highest_level if obj.account else 0

    def restriction_countdown(self, obj):
        if (
            hasattr(obj, 'playerrestriction')
            and obj.playerrestriction.end_date > timezone.now()
        ):
            return date_format(obj.playerrestriction.end_date, 'd/m/Y H:i')

    def formatted_date_joined(self, obj):
        return date_format(obj.date_joined, 'd/m/Y H:i')

    def formatted_last_login(self, obj):
        if obj.last_login:
            return date_format(obj.last_login, 'd/m/Y H:i')

    is_verified.boolean = True
    coins.short_description = 'RC Wallet'
    coins.admin_order_field = 'account__coins'
    level.admin_order_field = 'account__level'
    level_points.admin_order_field = 'account__level_points'
    report_points.admin_order_field = 'reports_received__report_points'
    restriction_countdown.short_description = 'Restriction ETA'
    formatted_date_joined.short_description = 'Date joined'
    formatted_last_login.short_description = 'Last login'

    @action(
        label=_('Assume Identity'),
        description=_('Assume a user identity and use the application as the user'),
    )
    def assume_identity(self, request, obj):
        if obj.is_staff:
            return

        token = obj.auth.get_token()
        if not token:
            obj.auth.create_token()
            token = obj.auth.token

        models.IdentityManager.objects.create(user=obj, agent=request.user)
        return HttpResponseRedirect(settings.FRONT_END_AUTH_URL.format(token))

    def get_change_actions(self, request, object_id, form_url):
        actions = super().get_change_actions(request, object_id, form_url)
        actions = list(actions)

        obj = self.model.objects.get(pk=object_id)
        if obj.is_staff:
            actions.remove('assume_identity')

        return actions

    change_actions = ('assume_identity',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            fieldsets = deepcopy(fieldsets)
            for fieldset in fieldsets:
                for field in ['is_staff', 'is_superuser', 'groups']:
                    if field in fieldset[1]['fields']:
                        fieldset[1]['fields'] = tuple(
                            x for x in fieldset[1]['fields'] if x != field
                        )
        return fieldsets

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if hasattr(form.instance, '_save_account'):
            form.instance._save_account.save()

    def get_formsets_with_inlines(self, request, obj=None):
        if obj is None:
            return []
        return super().get_formsets_with_inlines(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['steamid', 'username']
        return self.readonly_fields


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


@admin.register(models.AccountReport)
class AccountReportAdmin(admin_mixins.SuperUserOnlyAdminMixin, admin.ModelAdmin):
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


class StaffUserListFilter(admin.SimpleListFilter):
    title = 'agents'
    parameter_name = "agent_id"

    def lookups(self, request, model_admin):
        staff_users = models.User.objects.filter(is_staff=True)
        return [(user.id, user.email) for user in staff_users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(agent__id__exact=self.value())

        return queryset


@admin.register(models.IdentityManager)
class IdentityManagerAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'agent',
        'timestamp',
    )
    ordering = ('-timestamp',)
    list_filter = [StaffUserListFilter]
    search_fields = [
        'user__email',
        'user__id',
        'user__account__steamid',
        'agent__email',
        'agent__id',
    ]
