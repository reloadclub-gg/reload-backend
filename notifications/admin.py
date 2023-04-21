from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from . import forms, models

User = get_user_model()


@admin.register(models.SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ('content', 'create_date', 'notified_users')
    ordering = ('create_date',)
    filter_horizontal = ('to_users',)
    form = forms.SystemNotificationCreationForm

    fieldsets = (
        (
            None,
            {
                'fields': (
                    'user_filter',
                    'to_users',
                    'content',
                )
            },
        ),
    )

    def notified_users(self, obj):
        return obj.to_users.count()

    notified_users.short_description = _('Notified users')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'to_users':
            if request.GET.get('online'):
                kwargs['queryset'] = User.online_users()
            else:
                kwargs['queryset'] = User.objects.filter(
                    is_active=True, is_superuser=False
                )

        return super().formfield_for_manytomany(db_field, request, **kwargs)
