# Generated by Django 4.2 on 2023-07-31 19:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0007_match_chat"),
    ]

    operations = [
        migrations.AlterField(
            model_name="match",
            name="status",
            field=models.CharField(
                choices=[
                    ("loading", "Loading"),
                    ("running", "Running"),
                    ("finished", "Finished"),
                    ("cancelled", "Cancelled"),
                ],
                default="loading",
                max_length=16,
            ),
        ),
    ]