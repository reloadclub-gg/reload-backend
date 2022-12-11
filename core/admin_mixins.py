from django.contrib import admin


class CannotDeleteModelAdminMixin(admin.ModelAdmin):
    """
    Checks weather the logged user has delete permissions of a model on admin.
    """

    def has_delete_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser


class CannotCreateModelAdminMixin(admin.ModelAdmin):
    """
    Checks weather the logged user has create permissions of a model on admin.
    """

    def has_add_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser


class CannotChangeModelAdminMixin(admin.ModelAdmin):
    """
    Checks weather the logged user has update permissions of a model on admin.
    """

    def has_change_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser


class ReadOnlyModelAdminMixin(
    CannotDeleteModelAdminMixin,
    CannotCreateModelAdminMixin,
    CannotChangeModelAdminMixin,
):
    pass
