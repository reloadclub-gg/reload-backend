# Generated by Django 4.2 on 2024-01-04 14:13

from django.db import migrations, models
import store.models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0006_box_featured_image_collection_featured_image_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="box",
            name="featured_image",
            field=models.FileField(upload_to=store.models.item_featured_media_path),
        ),
        migrations.AlterField(
            model_name="collection",
            name="featured_image",
            field=models.FileField(upload_to=store.models.item_featured_media_path),
        ),
        migrations.AlterField(
            model_name="item",
            name="featured_image",
            field=models.FileField(upload_to=store.models.item_featured_media_path),
        ),
    ]
