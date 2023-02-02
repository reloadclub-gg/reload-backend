# Generated by Django 4.2a1 on 2023-02-02 13:58

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AppSettings",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("text", "Text"),
                            ("integer", "Integer"),
                            ("boolean", "Boolean"),
                        ],
                        default="text",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("value", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("description", models.TextField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "App Settings",
                "verbose_name_plural": "App Settings",
            },
        ),
    ]
