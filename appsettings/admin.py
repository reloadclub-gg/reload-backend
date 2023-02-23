from django.contrib import admin
from django.urls import path

from .forms import AppSettingsForm
from .models import AppSettings
from .views import email_rendered_by_name_view, emails_view


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    form = AppSettingsForm
    list_display = ['id', 'kind', 'name', 'value', 'is_active']
    list_display_links = ['id', 'name']
    list_editable = ['is_active']
    list_filter = ['kind', 'is_active']
    search_fields = ['name']

    def get_urls(self):
        return super().get_urls() + [
            path(
                'emails',
                emails_view,
                name=f'{AppSettings._meta.app_label}_{AppSettings._meta.model_name}_emails',
                kwargs={'get_context': self.admin_site.each_context},
            ),
            path(
                'email-rendered-by-name/<str:name>',
                email_rendered_by_name_view,
                name=f'{AppSettings._meta.app_label}_{AppSettings._meta.model_name}_email_rendered',
            ),
        ]
