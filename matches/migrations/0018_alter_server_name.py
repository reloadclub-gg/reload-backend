# Generated by Django 4.2 on 2023-11-03 16:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0017_alter_betauser_steamid_hex"),
    ]

    operations = [
        migrations.AlterField(
            model_name="server",
            name="name",
            field=models.CharField(max_length=32, unique=True),
        ),
    ]
