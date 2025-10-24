import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = BASE_DIR / "src"
APPS_DIR = SRC_DIR / "apps"

def load_valid_envs():
    from dotenv import load_dotenv

    main_env = PROJECT_DIR / ".env"
    if main_env.exists():
        load_dotenv(main_env)

    ENV = os.getenv("ENV", "dev")

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