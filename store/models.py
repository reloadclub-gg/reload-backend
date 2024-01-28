from __future__ import annotations

import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

from core.utils import generate_random_string

from .tasks import repopulate_user_store

User = get_user_model()


def item_media_path(instance, filename):
    extension = os.path.splitext(filename)[1]
    random_id = generate_random_string()
    if hasattr(instance, 'handle'):
        new_filename = f'{random_id}__{instance.handle}{extension}'
        path = f'store/{instance.handle}/media/'
    else:
        new_filename = f'{random_id}__{instance.item.handle}{extension}'
        path = f'store/{instance.item.handle}/media/'

    return path, new_filename


def item_background_media_path(instance, filename):
    path, file = item_media_path(instance, filename)
    return f'{path}/background__{file}'


def item_foreground_media_path(instance, filename):
    path, file = item_media_path(instance, filename)
    return f'{path}/foreground__{file}'


def item_cover_media_path(instance, filename):
    path, file = item_media_path(instance, filename)
    return f'{path}/cover__{file}'


def item_featured_media_path(instance, filename):
    path, file = item_media_path(instance, filename)
    return f'{path}/featured__{file}'


def item_decorative_media_path(instance, filename):
    path, file = item_media_path(instance, filename)
    return f'{path}/decorative__{file}'


def item_alternative_media_path(instance, filename):
    path, file = item_media_path(instance, filename)
    random_id = generate_random_string()
    return f'{path}/{instance.media_type}s/{random_id}__{file}'


class Box(models.Model):
    class Meta:
        verbose_name_plural = 'boxes'

    name = models.CharField(max_length=128)
    handle = models.CharField(max_length=128, unique=True, editable=False)
    owners = models.ManyToManyField(User, through='UserBox')
    price = models.PositiveIntegerField()
    create_date = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=False)
    description = models.TextField()
    discount = models.IntegerField(default=0)
    foreground_image = models.FileField(upload_to=item_foreground_media_path)
    cover_image = models.FileField(upload_to=item_cover_media_path)
    featured_image = models.FileField(
        upload_to=item_featured_media_path,
        null=True,
        blank=True,
    )
    featured = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.handle = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} (RC {self.price})'


class Collection(models.Model):
    name = models.CharField(max_length=128)
    handle = models.CharField(max_length=128, unique=True, editable=False)
    price = models.PositiveIntegerField()
    create_date = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=False)
    description = models.TextField()
    discount = models.IntegerField(default=0)
    foreground_image = models.FileField(upload_to=item_foreground_media_path)
    cover_image = models.FileField(upload_to=item_cover_media_path)
    featured_image = models.FileField(
        upload_to=item_featured_media_path,
        null=True,
        blank=True,
    )
    featured = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.handle = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} (RC {self.price})'


class Item(models.Model):
    class ItemType(models.TextChoices):
        WEAR = 'wear'
        WEAPON = 'weapon'
        DECORATIVE = 'decorative'
        PERSONA = 'persona'
        SPRAY = 'spray'

    class SubType(models.TextChoices):
        DEF = 'def'
        ATA = 'ata'
        CARD = 'card'
        PROFILE = 'profile'
        PISTOLS = 'pistols'
        SMGS = 'smgs'
        SHOTGUNS = 'shotguns'
        MACHINEGUNS = 'machineguns'
        RIFLES = 'rifles'

    class Weapon(models.TextChoices):
        PISTOLA = 'Pistola'
        RAPIDINHA = 'Rapidinha'
        NOVIDADE = '9idade'
        TRINTA_E_OITO = 'Trinta e Oito'
        MICRO = 'Micro'
        NOVA = 'Nova'
        DOZE = 'Doze'
        BULL = 'Bull'
        RAMBINHO = 'Rambinho'
        RAMBAO = 'Rambão'
        AK = 'AK'
        M4 = 'M4'
        TECO_TECO = 'Teco-Teco'
        SNIPER = 'Sniper'

    WEAPON_TYPES = {
        'pistols': ['Pistola', 'Rapidinha', '9idade', 'Trinta e Oito'],
        'smgs': ['Micro', 'Nova'],
        'shotguns': ['Doze', 'Bull'],
        'machineguns': ['Rambinho', 'Rambão'],
        'rifles': ['AK', 'M4', 'Teco-Teco', 'Sniper'],
    }

    owners = models.ManyToManyField(User, through='UserItem')
    name = models.CharField(max_length=128)
    item_type = models.CharField(max_length=32, choices=ItemType.choices)
    subtype = models.CharField(
        max_length=32,
        choices=SubType.choices,
        null=True,
        blank=True,
    )
    weapon = models.CharField(
        max_length=32,
        choices=Weapon.choices,
        null=True,
        blank=True,
    )
    handle = models.CharField(max_length=128, unique=True, editable=False)
    price = models.PositiveIntegerField()
    create_date = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True)
    is_available = models.BooleanField(default=False)
    description = models.TextField()
    discount = models.IntegerField(default=0)
    foreground_image = models.FileField(upload_to=item_foreground_media_path)
    cover_image = models.FileField(upload_to=item_cover_media_path)
    featured_image = models.FileField(
        upload_to=item_featured_media_path,
        null=True,
        blank=True,
    )
    decorative_image = models.ImageField(
        upload_to=item_decorative_media_path,
        null=True,
        blank=True,
    )
    box = models.ForeignKey(Box, on_delete=models.CASCADE, null=True, blank=True)
    box_draw_chance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    featured = models.BooleanField(default=False)
    is_starter = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['handle']),
            models.Index(fields=['price']),
            models.Index(fields=['is_available']),
            models.Index(fields=['release_date']),
        ]

    def save(self, *args, **kwargs):
        subtype_handle = f'-{self.subtype}' if self.subtype else ''
        weapon_handle = f'-{self.weapon}' if self.weapon else ''
        self.handle = (
            f'{self.item_type}{subtype_handle}{weapon_handle}-{slugify(self.name)}'
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} (RC {self.price})'


class ItemMedia(models.Model):
    class MediaType(models.TextChoices):
        VIDEO = 'video'
        IMAGE = 'image'

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    file = models.FileField(upload_to=item_alternative_media_path)
    media_type = models.CharField(max_length=16, choices=MediaType.choices)


class UserItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    in_use = models.BooleanField(default=False)
    can_use = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'item']
        indexes = [models.Index(fields=['in_use'])]
        ordering = ['item__id']

    def save(self, *args, **kwargs):
        if not self._state.adding:
            existing = UserItem.objects.filter(
                user=self.user,
                item__item_type=self.item.item_type,
                item__subtype=self.item.subtype,
                item__weapon=self.item.weapon,
            ).exclude(pk=self.pk)

            existing.update(in_use=False)
        super(UserItem, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.item.name} (RC {self.item.price})'


class UserBox(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    box = models.ForeignKey(Box, on_delete=models.CASCADE)
    purchase_date = models.DateTimeField(auto_now_add=True)
    open_date = models.DateTimeField(null=True)
    can_open = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'user boxes'
        unique_together = ['user', 'box']
        indexes = [models.Index(fields=['can_open'])]
        ordering = ['box__id']

    def __str__(self):
        return f'{self.box.name} (RC {self.box.price})'


class UserStore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_rotation_date = models.DateTimeField()
    next_rotation_date = models.DateTimeField()
    items_ids = ArrayField(
        models.IntegerField(),
        name='items_ids',
        size=settings.STORE_LENGTH,
    )
    last_rotation_items_ids = ArrayField(
        models.IntegerField(),
        name='last_rotation_items_ids',
        size=settings.STORE_LENGTH,
    )

    class Meta:
        ordering = ['next_rotation_date', '-last_rotation_date']
        indexes = [models.Index(fields=['items_ids'])]

    # TODO: boxes
    @property
    def featured(self):
        user_items_ids = UserItem.objects.all().values_list('id', flat=True)
        featured_items = list(
            Item.objects.filter(
                featured=True,
                is_available=True,
            ).exclude(id__in=user_items_ids)
        )
        featured_collections = list(
            Collection.objects.filter(
                featured=True,
                is_available=True,
            ).exclude(item__id__in=user_items_ids)
        )

        return (featured_collections + featured_items)[
            : settings.STORE_FEATURED_MAX_LENGTH
        ]

    # TODO: boxes
    @property
    def products(self):
        return Item.objects.filter(id__in=self.items_ids)

    # TODO: boxes
    @staticmethod
    def populate(user: User) -> UserStore:
        now = timezone.now()
        next_rotation_date = now + timedelta(days=settings.STORE_ROTATION_DAYS)
        user_items_ids = UserItem.objects.all().values_list('id', flat=True)
        items_ids = list(
            Item.objects.filter(is_available=True)
            .exclude(id__in=user_items_ids)
            .order_by('?')
            .values_list(
                'id',
                flat=True,
            )[: settings.STORE_LENGTH]
        )

        if not hasattr(user, 'userstore'):
            UserStore.objects.create(
                user=user,
                next_rotation_date=next_rotation_date,
                last_rotation_date=now,
                items_ids=items_ids,
                last_rotation_items_ids=items_ids,
            )
        else:
            user.userstore.next_rotation_date = next_rotation_date
            user.userstore.last_rotation_date = now
            user.userstore.last_rotation_items_ids = user.userstore.items_ids
            user.userstore.items_ids = items_ids
            user.userstore.save()

        return user.userstore


class ProductTransaction(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open'
        COMPLETE = 'complete'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)
    complete_date = models.DateTimeField(blank=True, null=True)
    product_id = models.CharField(max_length=256)
    session_id = models.CharField(max_length=256, blank=True, null=True)
    amount = models.PositiveIntegerField()
    price = models.CharField(max_length=9)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )

    class Meta:
        verbose_name_plural = 'transactions'
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['product_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'{self.user.email}: {self.amount} x {self.price}'


@receiver(post_save, sender=Item)
def send_starter_item_to_users_signal(sender, instance, created, **kwargs):
    if instance.is_starter:
        users_ids = set(User.active_verified_users().values_list('id', flat=True))
        user_items = set(
            UserItem.objects.filter(user_id__in=users_ids, item=instance).values_list(
                'user_id', flat=True
            )
        )
        users_ids_without_item = users_ids - user_items
        user_items = [
            UserItem(user_id=user_id, item=instance)
            for user_id in users_ids_without_item
        ]
        UserItem.objects.bulk_create(user_items, batch_size=1000)


@receiver(post_save, sender=UserStore)
def schedule_user_store_repopulate_signal(sender, instance, created, **kwargs):
    repopulate_user_store.apply_async(
        (instance.user.id,),
        eta=instance.next_rotation_date,
        serializer='json',
    )
