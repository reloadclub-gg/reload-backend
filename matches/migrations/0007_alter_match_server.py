# Generated by Django 4.2rc1 on 2023-03-27 23:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0001_squashed_0006_alter_matchplayer_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="match",
            name="server",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="matches.server"
            ),
        ),
    ]