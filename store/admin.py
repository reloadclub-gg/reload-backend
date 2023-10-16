from django.contrib import admin
from django.utils import timezone
from django_object_actions import action

from core.admin_mixins import AreYouSureActionsAdminMixin

from . import models


class ItemMediaAdminInline(admin.TabularInline):
    model = models.ItemMedia
    extra = 0


@admin.register(models.Item)
class ItemAdmin(AreYouSureActionsAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'item_type',
        'subtype',
        'handle',
        'price',
        'is_available',
        'discount',
    )
    readonly_fields = ('release_date', 'is_available', 'handle')
    search_fields = (
        'name',
        'item_type',
        'subtype',
        'handle',
    )

    ordering = ('name', 'price', 'discount')
    list_filter = ('item_type', 'subtype', 'is_available', 'price')
    inlines = [ItemMediaAdminInline]

    @action(description='Add item on app store.')
    def publish(self, request, obj):
        if not request.user.is_superuser:
            return

        obj.release_date = timezone.now()
        obj.is_available = True
        obj.save()

    @action(description='Remove item from app store')
    def unpublish(self, request, obj):
        if not request.user.is_superuser:
            return

        obj.is_available = False
        obj.save()

    def get_change_actions(self, request, object_id, form_url):
        actions = super().get_change_actions(request, object_id, form_url)
        actions = list(actions)

        if not request.user.is_superuser:
            actions.remove('publish', 'unpublish')

        return actions

    change_actions = ('publish', 'unpublish')
    are_you_sure_actions = ('publish', 'unpublish')
    are_you_sure_prompt_f = 'Are you sure you want to {label} this item?'


@admin.register(models.Box)
class BoxAdmin(AreYouSureActionsAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'handle',
        'price',
        'is_available',
        'discount',
    )
    readonly_fields = ('release_date', 'is_available', 'handle')
    search_fields = (
        'name',
        'handle',
    )

    ordering = ('name', 'price', 'discount')
    list_filter = ('is_available', 'price')

    @action(description='Add box on app store.')
    def publish(self, request, obj):
        if not request.user.is_superuser:
            return

        obj.release_date = timezone.now()
        obj.is_available = True
        obj.save()

    @action(description='Remove box from app store')
    def unpublish(self, request, obj):
        if not request.user.is_superuser:
            return

        obj.is_available = False
        obj.save()

    def get_change_actions(self, request, object_id, form_url):
        actions = super().get_change_actions(request, object_id, form_url)
        actions = list(actions)

        if not request.user.is_superuser:
            actions.remove('publish', 'unpublish')

        return actions

    change_actions = ('publish', 'unpublish')
    are_you_sure_actions = ('publish', 'unpublish')
    are_you_sure_prompt_f = 'Are you sure you want to {label} this item?'


@admin.register(models.Collection)
class CollectionAdmin(AreYouSureActionsAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'handle',
        'price',
        'is_available',
        'discount',
    )
    readonly_fields = ('release_date', 'is_available', 'handle')
    search_fields = (
        'name',
        'handle',
    )

    ordering = ('name', 'price', 'discount')
    list_filter = ('is_available', 'price')

    @action(description='Add collection on app store.')
    def publish(self, request, obj):
        if not request.user.is_superuser:
            return

        obj.release_date = timezone.now()
        obj.is_available = True
        obj.save()

    @action(description='Remove collection from app store')
    def unpublish(self, request, obj):
        if not request.user.is_superuser:
            return

        obj.is_available = False
        obj.save()

    def get_change_actions(self, request, object_id, form_url):
        actions = super().get_change_actions(request, object_id, form_url)
        actions = list(actions)

        if not request.user.is_superuser:
            actions.remove('publish', 'unpublish')

        return actions

    change_actions = ('publish', 'unpublish')
    are_you_sure_actions = ('publish', 'unpublish')
    are_you_sure_prompt_f = 'Are you sure you want to {label} this item?'