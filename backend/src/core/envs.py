import os

from core.paths import PROJECT_DIR


def load_valid_envs():
    """Load environment variables from .env files based on the current environment (dev, prod, test)."""
    from dotenv import load_dotenv

    main_env = PROJECT_DIR / ".env"
    if main_env.exists():
        load_dotenv(main_env)

    ENV = os.environ.get("ENV", "dev")

    if ENV == "dev":
        load_dotenv(PROJECT_DIR / ".envs/dev/django.env")
        load_dotenv(PROJECT_DIR / ".envs/dev/postgres.env")
        load_dotenv(PROJECT_DIR / ".envs/dev/minio.env")
    elif ENV == "prod":
        load_dotenv(PROJECT_DIR / ".envs/prod/django.env")
    elif ENV == "test":
        load_dotenv(PROJECT_DIR / ".envs/test/django.env")
    else:
        raise ValueError(f"Invalid environment: {ENV}")
