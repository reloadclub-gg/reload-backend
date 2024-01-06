import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext as _

from core.utils import generate_random_string

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
    background_image = models.ImageField(
        upload_to=item_background_media_path,
        null=True,
        blank=True,
    )
    foreground_image = models.FileField(upload_to=item_foreground_media_path)
    featured_image = models.FileField(upload_to=item_featured_media_path)
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
    background_image = models.ImageField(
        upload_to=item_background_media_path,
        null=True,
        blank=True,
    )
    foreground_image = models.FileField(upload_to=item_foreground_media_path)
    featured_image = models.FileField(upload_to=item_featured_media_path)
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

    owners = models.ManyToManyField(User, through='UserItem')
    name = models.CharField(max_length=128)
    item_type = models.CharField(max_length=32, choices=ItemType.choices)
    subtype = models.CharField(
        max_length=32,
        choices=SubType.choices,
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
    background_image = models.ImageField(
        upload_to=item_background_media_path,
        null=True,
        blank=True,
    )
    foreground_image = models.FileField(upload_to=item_foreground_media_path)
    featured_image = models.FileField(upload_to=item_featured_media_path)
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
        self.handle = f'{self.item_type}{subtype_handle}-{slugify(self.name)}'

        if self.box:
            total_chance = (
                Item.objects.filter(box=self.box)
                .exclude(id=self.id)
                .aggregate(models.Sum('box_draw_chance'))['box_draw_chance__sum']
                or 0
            )
            total_chance += self.box_draw_chance or 0

            if total_chance > 100:
                raise ValidationError(
                    _('The total sum of items on this box cannot be greater then 100%.')
                )

        if self.item_type == Item.ItemType.DECORATIVE:
            if not self.decorative_image:
                raise ValidationError(_('Decorative must have a decorative image.'))

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
