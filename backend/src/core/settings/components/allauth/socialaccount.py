import os
from typing import TypedDict


class GoogleOAuthApp(TypedDict, total=False):
    """Konfiguracja pojedynczej aplikacji Google OAuth dla allauth."""

    client_id: str
    secret: str
    key: str
    settings: dict[str, bool]


# Email jako główny identyfikator – username opcjonalne, unikalne (NULL ≠ duplikat w PostgreSQL)
SOCIALACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_ADAPTER = "core.services.allauth.social_adapter.SocialAccountAdapter"

GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
GOOGLE_OAUTH_ANDROID_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_ANDROID_CLIENT_ID", "")

GOOGLE_OAUTH_APPS: list[GoogleOAuthApp] = [
    {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "key": "",
    }
]

if GOOGLE_OAUTH_ANDROID_CLIENT_ID:
    GOOGLE_OAUTH_APPS.append(
        {
            "client_id": GOOGLE_OAUTH_ANDROID_CLIENT_ID,
            "secret": "",
            "key": "",
            "settings": {"hidden": True},
        }
    )

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": GOOGLE_OAUTH_APPS,
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "EMAIL_AUTHENTICATION": True,
    },
    "facebook": {
        "APP": {
            "client_id": os.environ.get("FACEBOOK_OAUTH_CLIENT_ID", ""),
            "secret": os.environ.get("FACEBOOK_OAUTH_CLIENT_SECRET", ""),
            "key": "",
        },
        "METHOD": "oauth2",
        "SCOPE": ["email", "public_profile"],
        "FIELDS": ["id", "email", "name", "first_name", "last_name"],
        "EXCHANGE_TOKEN": True,
        "VERIFIED_EMAIL": True,
    },
}
