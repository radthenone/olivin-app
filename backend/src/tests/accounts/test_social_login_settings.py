from __future__ import annotations

from allauth.socialaccount import app_settings as socialaccount_settings
from django.conf import settings


def test_social_login_does_not_authenticate_existing_user_by_email():
    """Login społecznościowy nie wpina się w istniejące konto po samym e-mailu."""
    assert socialaccount_settings.EMAIL_AUTHENTICATION is False
    assert settings.SOCIALACCOUNT_PROVIDERS["google"]["EMAIL_AUTHENTICATION"] is False
