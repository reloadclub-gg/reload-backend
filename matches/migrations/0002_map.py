# Generated by Django 4.2 on 2023-07-01 05:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Map",
            fields=[
                ("id", models.BigIntegerField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=32)),
                ("sys_name", models.CharField(max_length=32)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
    ]
