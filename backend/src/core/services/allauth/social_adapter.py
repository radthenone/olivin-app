from typing import Any, cast

from allauth.account.internal.emailkit import valid_email_or_none
from allauth.account.utils import user_email, user_field
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialLogin
from django.db import transaction

from apps.accounts.models import CustomUser
from apps.accounts.services import ensure_profile_for_user


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """Zapisuje social signup i zakłada powiązany profil."""
        with transaction.atomic():
            user = super().save_user(request, sociallogin, form)
            ensure_profile_for_user(user)
            return user

    def populate_user(
        self,
        request: Any,
        sociallogin: SocialLogin,
        data: dict[str, Any],
    ) -> CustomUser:
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        name = data.get("name", "")
        if sociallogin.user is None:
            raise ValueError("SocialLogin nie zawiera użytkownika do uzupełnienia.")

        user = cast(CustomUser, sociallogin.user)

        user_field(user, "username", None)
        user_email(user, valid_email_or_none(email) or "")
        name_parts = (name or "").partition(" ")
        user_field(user, "first_name", first_name or name_parts[0])
        user_field(user, "last_name", last_name or name_parts[2])

        return user

    def is_open_for_signup(self, request, sociallogin: SocialLogin) -> bool:
        email = sociallogin.account.extra_data.get("email")
        if not email:
            return False
        return super().is_open_for_signup(request, sociallogin)
