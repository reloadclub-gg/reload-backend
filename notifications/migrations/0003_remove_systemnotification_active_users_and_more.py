# Generated by Django 4.2 on 2023-04-20 16:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0002_remove_systemnotification_to_ids_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="systemnotification",
            name="active_users",
        ),
        migrations.RemoveField(
            model_name="systemnotification",
            name="online_users",
        ),
    ]
