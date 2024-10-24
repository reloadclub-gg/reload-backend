# Generated by Django 4.2 on 2023-12-11 20:04

from django.db import migrations, models
import store.models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0003_item_decorative_image_alter_item_item_type_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="box",
            name="background_image",
            field=models.ImageField(upload_to=store.models.item_background_media_path),
        ),
        migrations.AlterField(
            model_name="box",
            name="foreground_image",
            field=models.FileField(upload_to=store.models.item_foreground_media_path),
        ),
        migrations.AlterField(
            model_name="collection",
            name="background_image",
            field=models.ImageField(upload_to=store.models.item_background_media_path),
        ),
        migrations.AlterField(
            model_name="collection",
            name="foreground_image",
            field=models.FileField(upload_to=store.models.item_foreground_media_path),
        ),
        migrations.AlterField(
            model_name="item",
            name="background_image",
            field=models.ImageField(upload_to=store.models.item_background_media_path),
        ),
        migrations.AlterField(
            model_name="item",
            name="decorative_image",
            field=models.ImageField(
                blank=True, null=True, upload_to=store.models.item_decorative_media_path
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="foreground_image",
            field=models.FileField(upload_to=store.models.item_foreground_media_path),
        ),
        migrations.AlterField(
            model_name="itemmedia",
            name="file",
            field=models.FileField(upload_to=store.models.item_alternative_media_path),
        ),
    ]
