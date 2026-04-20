import os

# Email jako główny identyfikator – username opcjonalne, unikalne (NULL ≠ duplikat w PostgreSQL)
SOCIALACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_ADAPTER = "core.services.allauth.social_adapter.SocialAccountAdapter"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
            "secret": os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""),
            "key": "",
        },
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
