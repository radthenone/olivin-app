import os

from core.paths import PROJECT_DIR


def load_valid_envs():
    """Load environment variables from .env files based on the current environment (dev, prod, test)."""
    from dotenv import load_dotenv

    main_env = PROJECT_DIR / ".env"
    if main_env.exists():
        load_dotenv(main_env)

    ENV = os.environ.get("DJANGO_ENV", "dev")

    if ENV == "dev":
        load_dotenv(PROJECT_DIR / ".envs/dev/backend/django.env")
        load_dotenv(PROJECT_DIR / ".envs/dev/backend/db.env")
        load_dotenv(PROJECT_DIR / ".envs/dev/backend/cache_broker.env")
        load_dotenv(PROJECT_DIR / ".envs/dev/backend/broker.env")
        load_dotenv(PROJECT_DIR / ".envs/dev/backend/email.env")
        load_dotenv(PROJECT_DIR / ".envs/dev/backend/s3.env")
        load_dotenv(PROJECT_DIR / ".envs/dev/backend/authorization.env")
    elif ENV == "prod":
        "load prod envs"
    elif ENV == "test":
        "load test envs"
    else:
        raise ValueError(f"Invalid environment: {ENV}")
