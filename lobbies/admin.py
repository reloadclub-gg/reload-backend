from django.contrib import admin
from django.core.paginator import Paginator

from . import models


class EmptyPaginator(Paginator):
    def page(self, number):
        return self._get_page([], number, self)


@admin.register(models.LobbyAdminModel)
class LobbyAdminModelAdmin(admin.ModelAdmin):
    show_full_result_count = False
    change_list_template = "lobbies/admin/change_list.html"

    def get_queryset(self, request):
        return models.LobbyAdminModel.objects.none()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        objects = models.Lobby.get_active_lobbies()

        extra_context = extra_context or {}
        extra_context['objects'] = objects
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
