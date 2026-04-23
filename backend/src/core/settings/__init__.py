import os

from split_settings.tools import include, optional

base_settings = [
    "components/apps.py",
    "components/middleware.py",
    "components/database.py",
    "components/auth.py",
    "components/storage.py",
    "components/celery.py",
    "components/email.py",
    "components/security.py",
    "components/session.py",
    "components/allauth/__init__.py",
    "base.py",
]

env = os.environ.get("DJANGO_ENVIRONMENT", "").lower()
debug = os.environ.get("DJANGO_DEBUG", "1")

if env == "testing":
    include(*base_settings, "testing.py")
elif debug == "1" or env == "development":
    include(*base_settings, "development.py", optional("local.py"))
else:
    include(*base_settings, "production.py", optional("local.py"))
