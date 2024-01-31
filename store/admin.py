import re
from decimal import Decimal

from django.contrib import admin
from django.utils import timezone
from django_object_actions import action

from core.admin_mixins import AreYouSureActionsAdminMixin

from . import forms, models


@admin.action(description="Mark selected items as published on store")
def make_published(modeladmin, request, queryset):
    queryset.update(is_available=True)


@admin.action(description="Mark selected items as unpublished on store")
def make_unpublished(modeladmin, request, queryset):
    queryset.update(is_available=False)


class ItemMediaAdminInline(admin.TabularInline):
    model = models.ItemMedia
    extra = 0


@admin.register(models.Item)
class ItemAdmin(AreYouSureActionsAdminMixin, admin.ModelAdmin):
    form = forms.ItemForm
    actions = [make_published, make_unpublished]
    list_display = (
        'name',
        'item_type',
        'subtype',
        'handle',
        'price',
        'is_available',
        'discount',
        'box',
        'collection',
        'is_starter',
    )
    readonly_fields = ('release_date', 'is_available', 'handle')
    search_fields = (
        'name',
        'item_type',
        'subtype',
        'handle',
        'box__name',
        'collection__name',
    )

    ordering = ('-create_date', 'name', 'price', 'discount')
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
            actions.remove('publish')
            actions.remove('unpublish')

        return actions

    change_actions = ('publish', 'unpublish')
    are_you_sure_actions = ('publish', 'unpublish')
    are_you_sure_prompt_f = 'Are you sure you want to {label} this item?'


@admin.register(models.Box)
class BoxAdmin(AreYouSureActionsAdminMixin, admin.ModelAdmin):
    form = forms.BoxForm
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

    ordering = ('-create_date', 'name', 'price', 'discount')
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
            actions.remove('publish')
            actions.remove('unpublish')

        return actions

    change_actions = ('publish', 'unpublish')
    are_you_sure_actions = ('publish', 'unpublish')
    are_you_sure_prompt_f = 'Are you sure you want to {label} this item?'


@admin.register(models.Collection)
class CollectionAdmin(AreYouSureActionsAdminMixin, admin.ModelAdmin):
    form = forms.CollectionForm
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

    ordering = ('-create_date', 'name', 'price', 'discount')
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
            actions.remove('publish')
            actions.remove('unpublish')

        return actions

    change_actions = ('publish', 'unpublish')
    are_you_sure_actions = ('publish', 'unpublish')
    are_you_sure_prompt_f = 'Are you sure you want to {label} this item?'


@admin.register(models.ProductTransaction)
class ProductTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'create_date',
        'complete_date',
        'amount',
        'price',
        'status',
    )
    search_fields = ('user__email',)
    ordering = ('-create_date', '-complete_date', 'price', 'amount')
    list_filter = ('amount', 'status', 'price')

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['now'] = timezone.now()

        today_transactions = models.ProductTransaction.objects.filter(
            complete_date__day=timezone.now().day,
            status=models.ProductTransaction.Status.COMPLETE,
        ).values_list('price', flat=True)
        today_total = sum(
            Decimal(re.sub(r'[^\d,]', '', price).replace(',', '.'))
            for price in today_transactions
            if price
        )

        month_transactions = models.ProductTransaction.objects.filter(
            complete_date__month=timezone.now().month,
            status=models.ProductTransaction.Status.COMPLETE,
        ).values_list('price', flat=True)
        month_total = sum(
            Decimal(re.sub(r'[^\d,]', '', price).replace(',', '.'))
            for price in month_transactions
            if price
        )

        all_transactions = models.ProductTransaction.objects.filter(
            status=models.ProductTransaction.Status.COMPLETE,
        ).values_list('price', flat=True)
        all_total = sum(
            Decimal(re.sub(r'[^\d,]', '', price).replace(',', '.'))
            for price in all_transactions
            if price
        )

        extra_context['today_total'] = today_total
        extra_context['month_total'] = month_total
        extra_context['all_total'] = all_total

        return super().changelist_view(request, extra_context=extra_context)
