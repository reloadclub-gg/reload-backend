from django.contrib import admin
from django_object_actions import DjangoObjectActions


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


class SuperUserOnlyAdminMixin(admin.ModelAdmin):
    def has_module_permission(self, request) -> bool:
        return request.user.is_superuser


class AreYouSureActionsAdminMixin(DjangoObjectActions):
    are_you_sure_actions = ()
    are_you_sure_prompt_f = "Are you sure you want to {label} this object?"

    def __init__(self, *args, **kwargs):
        super(AreYouSureActionsAdminMixin, self).__init__(*args, **kwargs)
        for action in self.are_you_sure_actions:
            tool = getattr(self, action)
            label = getattr(tool, 'label', action).lower()
            are_you_sure_prompt = self.are_you_sure_prompt_f.format(
                tool=tool, label=label
            )
            tool.__dict__.setdefault('attrs', {})
            tool.__dict__['attrs'].setdefault(
                'onclick', f"""return confirm("{are_you_sure_prompt}");"""
            )
