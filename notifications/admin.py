from django.contrib import admin
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_object_actions import DjangoObjectActions, action

from . import forms, models

User = get_user_model()


@admin.register(models.SystemNotification)
class SystemNotificationAdmin(DjangoObjectActions, admin.ModelAdmin):
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

    @action(label=_('All active users'), description=_('List all active users'))
    def filter_active_users(self, request, obj):
        return HttpResponseRedirect(
            reverse('admin:notifications_systemnotification_change', args=(obj.id,))
        )

    @action(label=_('Online users'), description=_('List online users'))
    def filter_online_users(self, request, obj):
        return HttpResponseRedirect(
            reverse('admin:notifications_systemnotification_change', args=(obj.id,))
            + '?online=1'
        )

    change_actions = ('filter_online_users', 'filter_active_users')
