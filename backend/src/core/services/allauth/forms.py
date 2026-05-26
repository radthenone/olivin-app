from __future__ import annotations

from allauth.account.forms import SignupForm
from django.db import transaction

from apps.accounts.services import ensure_profile_for_user


class SignupWithProfileForm(SignupForm):
    """Tworzy użytkownika allauth i profil w jednej transakcji."""

    def save(self, request):
        """Zapisuje signup i zakłada profil dopiero po poprawnej walidacji."""
        with transaction.atomic():
            user = super().save(request)
            ensure_profile_for_user(user)
            return user
