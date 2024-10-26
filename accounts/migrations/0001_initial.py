# Generated by Django 4.2 on 2023-05-26 18:46

import accounts.models.user
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                (
                    "is_staff",
                    models.BooleanField(default=False, verbose_name="staff status"),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="active")),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "date_inactivation",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="date inactivation"
                    ),
                ),
                (
                    "date_email_update",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="latest email update date"
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
            managers=[
                ("objects", accounts.models.user.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("steamid", models.CharField(max_length=128)),
                ("username", models.CharField(max_length=64)),
                ("level", models.IntegerField(default=0)),
                ("level_points", models.IntegerField(default=0)),
                ("highest_level", models.IntegerField(default=0)),
                ("is_verified", models.BooleanField(default=False)),
                (
                    "verification_token",
                    models.CharField(
                        max_length=6,
                        validators=[django.core.validators.MinLengthValidator(6)],
                    ),
                ),
                ("report_points", models.IntegerField(default=0)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ReportAnalysis",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                (
                    "restriction_time",
                    models.IntegerField(help_text="In hours.", null=True),
                ),
                ("comments", models.TextField(blank=True, null=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis_set",
                        to="accounts.account",
                    ),
                ),
                (
                    "analyst",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.account",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Report",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "subject",
                    models.TextField(
                        choices=[
                            (0, "Hate Speech"),
                            (1, "Chat Abuse"),
                            (2, "Report Abuse"),
                            (3, "Bad Conduct"),
                            (4, "Anti Game"),
                            (5, "Account Sharing"),
                            (6, "Cheating"),
                        ]
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("comments", models.TextField(blank=True, null=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.account",
                    ),
                ),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reported_set",
                        to="accounts.account",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserLogin",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "ip_address",
                    models.CharField(
                        blank=True, editable=False, max_length=128, null=True
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "get_latest_by": "timestamp",
                "unique_together": {("user", "ip_address")},
            },
        ),
        migrations.CreateModel(
            name="Invite",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("datetime_created", models.DateTimeField(auto_now_add=True)),
                ("datetime_updated", models.DateTimeField(auto_now=True)),
                ("email", models.EmailField(max_length=254)),
                (
                    "datetime_accepted",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                (
                    "owned_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.account",
                    ),
                ),
            ],
            options={
                "unique_together": {("owned_by", "email")},
            },
        ),
    ]
