# Generated by Django 4.2a1 on 2023-02-04 16:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_date_email_update"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="date_inactivation",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="date inactivation"
            ),
        ),
    ]
