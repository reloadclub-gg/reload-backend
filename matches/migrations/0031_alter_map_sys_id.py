# Generated by Django 4.2 on 2024-03-27 18:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0030_map_sys_id_alter_map_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="map",
            name="sys_id",
            field=models.IntegerField(unique=True),
        ),
    ]
