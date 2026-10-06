from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "apps.notifications"

    def ready(self) -> None:
        # Import dla efektu ubocznego: rejestruje odbiorniki sygnałów.
        from apps.notifications import signals  # noqa: F401
