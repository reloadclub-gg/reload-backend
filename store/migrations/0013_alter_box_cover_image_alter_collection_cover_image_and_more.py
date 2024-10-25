# Generated by Django 4.2 on 2024-01-26 20:14

from django.db import migrations, models
import store.models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0012_remove_box_background_image_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="box",
            name="cover_image",
            field=models.FileField(upload_to=store.models.item_cover_media_path),
        ),
        migrations.AlterField(
            model_name="collection",
            name="cover_image",
            field=models.FileField(upload_to=store.models.item_cover_media_path),
        ),
        migrations.AlterField(
            model_name="item",
            name="cover_image",
            field=models.FileField(upload_to=store.models.item_cover_media_path),
        ),
    ]
