# Generated by Django 4.2 on 2023-08-05 18:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0002_alter_item_subtype"),
    ]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="subtype",
            field=models.CharField(
                blank=True,
                choices=[("def", "Def"), ("ata", "Ata")],
                max_length=32,
                null=True,
            ),
        ),
    ]
