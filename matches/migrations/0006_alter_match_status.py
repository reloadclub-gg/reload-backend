# Generated by Django 4.2 on 2023-07-20 06:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0005_remove_server_key"),
    ]

    operations = [
        migrations.AlterField(
            model_name="match",
            name="status",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (0, "Loading"),
                    (1, "Running"),
                    (2, "Finished"),
                    (3, "Cancelled"),
                ],
                default=0,
                null=True,
            ),
        ),
    ]
