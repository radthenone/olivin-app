import os

from core.paths import PROJECT_DIR

DEV_ENV_FILES = (
    "django.env",
    "db.env",
    "cache_broker.env",
    "broker.env",
    "email.env",
    "s3.env",
    "authorization.env",
)


def load_valid_envs():
    """Load `.env` files for the environment named by `DJANGO_ENVIRONMENT`.

    Testy (`testing`) nie czytają żadnych plików — wynik nie zależy od tego,
    co leży na maszynie dewelopera. Pozostałe środowiska ładują `.env`
    i `.envs/dev`; zmienne już ustawione (compose, CI) mają pierwszeństwo.
    """
    from dotenv import load_dotenv

    if os.environ.get("DJANGO_ENVIRONMENT", "").lower() == "testing":
        return

    load_dotenv(PROJECT_DIR / ".env")
    for name in DEV_ENV_FILES:
        load_dotenv(PROJECT_DIR / ".envs/dev/backend" / name)
