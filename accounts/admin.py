from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext as _
from social_django.models import Association, Nonce, UserSocialAuth

from core import admin_mixins

from .models import User, UserLogin

admin.site.unregister(Group)
if settings.ENVIRONMENT == 'production':
    admin.site.unregister(UserSocialAuth)
    admin.site.unregister(Association)
    admin.site.unregister(Nonce)


class UserLoginAdminInline(admin.TabularInline):
    model = UserLogin
    readonly_fields = ['timestamp', 'ip_address']
    extra = 1

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(User)
class UserAdmin(admin_mixins.ReadOnlyModelAdminMixin, DjangoUserAdmin):
    fieldsets = (
        (
            _('Account'),
            {
                'fields': (
                    'steamid',
                    'username',
                    'level',
                    'level_points',
                    'report_points',
                )
            },
        ),
        (_('Important Dates'), {'fields': ('date_joined', 'last_login')}),
        (
            _('Statuses'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'is_verified',
                    'is_online',
                )
            },
        ),
        (_('Activation'), {'fields': ('verification_token',)}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2'),
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
        'report_points',
        'level',
        'level_points',
    )
    readonly_fields = [
        'email',
        'steamid',
        'username',
        'last_login',
        'date_joined',
        'is_active',
        'is_staff',
        'is_superuser',
        'is_verified',
        'is_online',
        'level',
        'level_points',
        'verification_token',
        'report_points',
    ]
    search_fields = ('email', 'date_joined')
    ordering = ('email', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff')
    inlines = [UserLoginAdminInline]

    def is_online(self, obj):
        return obj.is_online

    def steamid(self, obj):
        return obj.steam_user.steamid

    def username(self, obj):
        return obj.steam_user.username

    def is_verified(self, obj):
        return obj.account.is_verified if obj.account else False

    def report_points(self, obj):
        return obj.account.report_points if obj.account else 0

    def level(self, obj):
        return obj.account.level if obj.account else 0

    def level_points(self, obj):
        return obj.account.level_points if obj.account else 0

    def verification_token(self, obj):
        return obj.account.verification_token if obj.account else None

    is_online.boolean = True
    is_verified.boolean = True
