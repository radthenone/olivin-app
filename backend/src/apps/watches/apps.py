from django.apps import AppConfig


class WatchesConfig(AppConfig):
    name = "apps.watches"

    def ready(self) -> None:
        from apps.watches import signals  # noqa: F401
