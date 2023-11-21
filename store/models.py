import os

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext as _

User = get_user_model()


def item_media_path(instance, filename):
    extension = os.path.splitext(filename)[1]

    if hasattr(instance, 'handle'):
        new_filename = f'{instance.handle}{extension}'
        return f'store/{instance.handle}/media/{new_filename}'
    else:
        new_filename = f'{instance.item.handle}{extension}'
        return f'store/{instance.item.handle}/media/{new_filename}'


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
    background_image = models.ImageField(upload_to=item_media_path)
    foreground_image = models.FileField(upload_to=item_media_path)
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
    background_image = models.ImageField(upload_to=item_media_path)
    foreground_image = models.FileField(upload_to=item_media_path)
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
        CONSUMABLE = 'consumable'
        PERSONA = 'persona'
        SPRAY = 'spray'

    class SubType(models.TextChoices):
        DEF = 'def'
        ATA = 'ata'

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
    background_image = models.ImageField(upload_to=item_media_path)
    foreground_image = models.FileField(upload_to=item_media_path)
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

        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} (RC {self.price})'


class ItemMedia(models.Model):
    class MediaType(models.TextChoices):
        VIDEO = 'video'
        IMAGE = 'image'

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    file = models.FileField(upload_to=item_media_path)
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

    def save(self, *args, **kwargs):
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
