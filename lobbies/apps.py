from django.apps import AppConfig


class LobbiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'lobbies'

    def ready(self):
        import lobbies.signals  # noqa
