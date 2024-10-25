# Generated by Django 4.2 on 2024-01-26 20:14

from django.db import migrations, models
import store.models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0011_alter_item_subtype"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="box",
            name="background_image",
        ),
        migrations.RemoveField(
            model_name="collection",
            name="background_image",
        ),
        migrations.RemoveField(
            model_name="item",
            name="background_image",
        ),
        migrations.AddField(
            model_name="box",
            name="cover_image",
            field=models.FileField(
                default="default.png", upload_to=store.models.item_cover_media_path
            ),
        ),
        migrations.AddField(
            model_name="collection",
            name="cover_image",
            field=models.FileField(
                default="default.png", upload_to=store.models.item_cover_media_path
            ),
        ),
        migrations.AddField(
            model_name="item",
            name="cover_image",
            field=models.FileField(
                default="default.png", upload_to=store.models.item_cover_media_path
            ),
        ),
        migrations.AlterField(
            model_name="box",
            name="featured_image",
            field=models.FileField(
                blank=True, null=True, upload_to=store.models.item_featured_media_path
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="featured_image",
            field=models.FileField(
                blank=True, null=True, upload_to=store.models.item_featured_media_path
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="featured_image",
            field=models.FileField(
                blank=True, null=True, upload_to=store.models.item_featured_media_path
            ),
        ),
    ]
