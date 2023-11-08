# Generated by Django 4.2 on 2023-11-08 01:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0002_alter_userbox_unique_together_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="userbox",
            index=models.Index(
                fields=["can_open"], name="store_userb_can_ope_e27fb8_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="useritem",
            index=models.Index(fields=["in_use"], name="store_useri_in_use_7f58da_idx"),
        ),
    ]
