# Generated by Django 4.2 on 2023-07-29 17:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0006_alter_match_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="match",
            name="chat",
            field=models.JSONField(null=True),
        ),
    ]
