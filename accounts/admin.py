from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group

from social_django.models import UserSocialAuth, Association, Nonce

from core import admin_mixins
from .models import Account, User, UserLogin, Invite

admin.site.unregister(Group)
if settings.ENVIRONMENT == 'production':
    admin.site.unregister(UserSocialAuth)
    admin.site.unregister(Association)
    admin.site.unregister(Nonce)


@admin.register(User)
class UserAdmin(admin_mixins.ReadOnlyModelAdminMixin, DjangoUserAdmin):
    fieldsets = (
        ('Personal info', {'fields': ('email', 'password')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
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
        'id',
        'email',
        'date_joined',
        'last_login',
        'is_active',
        'is_online',
    )
    search_fields = ('email', 'date_joined')
    ordering = ('email', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff')

    def is_online(self, obj):
        return obj.is_online

    is_online.boolean = True


@admin.register(UserLogin)
class UserLoginAdmin(admin_mixins.ReadOnlyModelAdminMixin):
    list_display = ('user', 'timestamp', 'ip_address')
    ordering = ('timestamp', 'ip_address')
    search_fields = ('ip_address',)


@admin.register(Account)
class AccountAdmin(admin_mixins.ReadOnlyModelAdminMixin):
    list_display = (
        'user',
        'level',
        'level_points',
        'username',
        'steamid',
        'is_verified',
    )
    search_fields = ('user__email',)
    ordering = ('user__date_joined',)
    list_filter = ('is_verified',)
    readonly_fields = ('verification_token',)

    def steamid(self, obj):
        return obj.user.steam_user.steamid

    def username(self, obj):
        return obj.user.steam_user.username


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'owned_by',
        'datetime_created',
        'datetime_updated',
        'datetime_accepted',
    )
    search_fields = ('email', 'owned_by__user__email')
    ordering = ('datetime_created',)
