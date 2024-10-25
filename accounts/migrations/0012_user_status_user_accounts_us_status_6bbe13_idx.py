# Generated by Django 4.2 on 2023-10-23 01:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_alter_account_social_handles"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="status",
            field=models.CharField(
                choices=[
                    ("online", "Online"),
                    ("offline", "Offline"),
                    ("teaming", "Teaming"),
                    ("queued", "Queued"),
                    ("in_game", "In Game"),
                ],
                default="offline",
                max_length=16,
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["status"], name="accounts_us_status_6bbe13_idx"),
        ),
    ]
