# Generated by Django 4.2 on 2023-07-31 21:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0008_alter_match_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="match",
            name="status",
            field=models.CharField(
                choices=[
                    ("loading", "Loading"),
                    ("warmup", "Warmup"),
                    ("running", "Running"),
                    ("finished", "Finished"),
                    ("cancelled", "Cancelled"),
                ],
                default="loading",
                max_length=16,
            ),
        ),
    ]
