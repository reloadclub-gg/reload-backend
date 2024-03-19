from django.contrib import admin
from django.contrib.auth import get_user_model

from . import forms, models

User = get_user_model()


@admin.register(models.Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ("name", "users", "allowed_to")
    form = forms.FeatureCreationForm

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "allowed_to",
                    "user_filter",
                    "selected_users",
                )
            },
        ),
    )

    def users(self, obj):
        return list(obj.selected_users.all().values_list("email", flat=True)) or None

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "selected_users":
            if request.GET.get("online"):
                online_users_ids = [user.id for user in User.online_users()]
                kwargs["queryset"] = User.objects.filter(id__in=online_users_ids)
            else:
                kwargs["queryset"] = User.objects.filter(
                    is_active=True,
                    is_superuser=False,
                )

        return super().formfield_for_manytomany(db_field, request, **kwargs)
