# Generated by Django 4.2 on 2024-02-20 16:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("matches", "0021_alter_map_weight"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="match",
            name="game_type",
        ),
        migrations.AddField(
            model_name="match",
            name="match_type",
            field=models.CharField(
                choices=[
                    ("default", "Default"),
                    ("deathmatch", "Deathmatch"),
                    ("safezone", "Safezone"),
                ],
                default="default",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="match",
            name="game_mode",
            field=models.CharField(
                choices=[("custom", "Custom"), ("competitive", "Competitive")],
                default="competitive",
                max_length=16,
            ),
        ),
    ]
