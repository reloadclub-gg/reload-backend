from django.apps import AppConfig


class AppSettingsConfig(AppConfig):
    name = 'appsettings'

    def ready(self):
        import appsettings.signals  # noqa
