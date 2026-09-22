from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = "apps.orders"

    def ready(self) -> None:
        # Import dla efektu ubocznego: rejestruje odbiorniki sygnałów.
        from apps.orders import signals  # noqa: F401
