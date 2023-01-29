from django.contrib import admin

from .forms import AppSettingsForm
from .models import AppSettings


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    form = AppSettingsForm
    list_display = ['id', 'kind', 'name', 'value', 'is_active']
    list_display_links = ['id', 'name']
    list_editable = ['is_active']
    list_filter = ['kind', 'is_active']
    search_fields = ['name']
