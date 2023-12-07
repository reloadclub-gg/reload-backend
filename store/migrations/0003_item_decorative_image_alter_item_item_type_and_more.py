# Generated by Django 4.2 on 2023-12-07 15:31

from django.db import migrations, models
import store.models


class Migration(migrations.Migration):
    dependencies = [
        (
            "store",
            "0002_remove_producttransaction_store_produ_transac_bb1fda_idx_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="decorative_image",
            field=models.ImageField(
                blank=True, null=True, upload_to=store.models.item_media_path
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="item_type",
            field=models.CharField(
                choices=[
                    ("wear", "Wear"),
                    ("weapon", "Weapon"),
                    ("decorative", "Decorative"),
                    ("persona", "Persona"),
                    ("spray", "Spray"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="subtype",
            field=models.CharField(
                blank=True,
                choices=[
                    ("def", "Def"),
                    ("ata", "Ata"),
                    ("card", "Card"),
                    ("profile", "Profile"),
                ],
                max_length=32,
                null=True,
            ),
        ),
    ]
