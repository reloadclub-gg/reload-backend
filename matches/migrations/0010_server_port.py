# Generated by Django 4.2 on 2023-08-28 19:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0009_alter_match_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="server",
            name="port",
            field=models.IntegerField(default=30120),
        ),
    ]
