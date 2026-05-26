from __future__ import annotations

from typing import Any, Mapping

from apps.accounts.models import Profile
from apps.accounts.serializers import ProfileSerializer


def ensure_profile_for_user(user: Any) -> Profile:
    """Tworzy profil użytkownika, jeśli jeszcze nie istnieje."""
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            "first_name": getattr(user, "first_name", ""),
            "last_name": getattr(user, "last_name", ""),
        },
    )
    return profile


def update_profile_from_signup_data(user: Any, data: Mapping[str, Any]) -> Profile:
    """Uzupełnia profil danymi przekazanymi razem z rejestracją."""
    profile = ensure_profile_for_user(user)
    normalized_data = {
        "first_name": data.get("first_name") or data.get("firstName") or "",
        "last_name": data.get("last_name") or data.get("lastName") or "",
        "date_of_birth": data.get("date_of_birth") or data.get("dateOfBirth") or None,
        "phone_number": data.get("phone_number") or data.get("phoneNumber") or "",
    }
    serializer = ProfileSerializer(profile, data=normalized_data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return profile
