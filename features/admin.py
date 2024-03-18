from django.contrib import admin
from django.contrib.auth import get_user_model

from . import forms, models

User = get_user_model()


@admin.register(models.Feature)
class Feature(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(models.FeaturePreview)
class FeaturePreviewAdmin(admin.ModelAdmin):
    list_display = ("feature", "early_adopters")
    form = forms.FeaturePreviewCreationForm

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user_filter",
                    "users",
                    "feature",
                )
            },
        ),
    )

    def early_adopters(self, obj):
        return obj.users.count()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "users":
            if request.GET.get("online"):
                online_users_ids = [user.id for user in User.online_users()]
                kwargs["queryset"] = User.objects.filter(id__in=online_users_ids)
            else:
                kwargs["queryset"] = User.objects.filter(
                    is_active=True, is_superuser=False
                )

        return super().formfield_for_manytomany(db_field, request, **kwargs)
