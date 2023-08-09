from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify

User = get_user_model()


def item_media_path(instance, filename):
    return f'items/{instance.id}/media/{filename}'


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
    handle = models.CharField(max_length=128, unique=True)
    price = models.IntegerField()
    create_date = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True)
    is_available = models.BooleanField(default=False)
    description = models.TextField()
    discount = models.IntegerField(default=0)
    background_image = models.ImageField(upload_to=item_media_path)
    foreground_image = models.FileField(upload_to=item_media_path)

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
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ItemMedia(models.Model):
    class MediaType(models.TextChoices):
        VIDEO = 'video'
        IMAGE = 'image'

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    file = models.FileField(upload_to=item_media_path)
    media_type = models.CharField(max_length=16, choices=MediaType.choices)


class Box(models.Model):
    items = models.ManyToManyField(Item, through='BoxItem')
    price = models.IntegerField()
    create_date = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    description = models.TextField()
    discount = models.IntegerField(default=0)
    background_image = models.ImageField(upload_to=item_media_path)
    foreground_image = models.FileField(upload_to=item_media_path)


class BoxItem(models.Model):
    box = models.ForeignKey(Box, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)
    draw_chance = models.DecimalField(max_digits=5, decimal_places=2)


class Collection(models.Model):
    items = models.ManyToManyField(Item, through='CollectionItem')
    price = models.IntegerField()
    create_date = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    description = models.TextField()
    discount = models.IntegerField(default=0)
    background_image = models.ImageField(upload_to=item_media_path)
    foreground_image = models.FileField(upload_to=item_media_path)


class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True)


class UserItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    box = models.ForeignKey(Box, on_delete=models.SET_NULL, null=True, blank=True)
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    purchase_date = models.DateTimeField(auto_now_add=True)
    in_use = models.BooleanField(default=False)
    open_date = models.DateTimeField(null=True)
