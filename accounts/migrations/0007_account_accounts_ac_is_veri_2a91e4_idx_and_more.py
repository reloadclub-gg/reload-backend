# Generated by Django 4.2 on 2023-07-22 18:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_identitymanager"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="account",
            index=models.Index(
                fields=["is_verified"], name="accounts_ac_is_veri_2a91e4_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="account",
            index=models.Index(
                fields=["steamid"], name="accounts_ac_steamid_35790e_idx"
            ),
        ),
    ]
