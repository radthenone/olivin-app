from __future__ import annotations

from typing import Any, Dict, cast

import pytest

from apps.accounts.serializers import ProfileSerializer
from tests.factories.accounts import ProfileFactory, UserFactory


@pytest.mark.django_db
class TestProfileSerializer:
    """Testy serializera ProfileSerializer."""

    def test_serializacja_podstawowych_pol(self):
        """Serializer powinien zwracać wymagane pola."""
        user = UserFactory(email="jan@test.com")
        profile = ProfileFactory(user=user, first_name="Jan", last_name="Kowalski")
        serializer = ProfileSerializer(profile)
        # Używamy dict() by uciszyć linter typów narzekający na '__getitem__' na ReturnDict
        data: Dict[str, Any] = dict(serializer.data)

        assert data["email"] == "jan@test.com"
        assert data["first_name"] == "Jan"
        assert data["last_name"] == "Kowalski"
        assert data["full_name"] == "Jan Kowalski"
        assert "role" in data

    def test_full_name_method_field(self):
        """full_name powinien być obliczany przez get_full_name."""
        profile = ProfileFactory(first_name="Anna", last_name="Nowak")
        serializer = ProfileSerializer(profile)
        data: Dict[str, Any] = dict(serializer.data)
        assert data["full_name"] == "Anna Nowak"

    def test_age_none_gdy_brak_daty_urodzenia(self):
        """age powinien wynosić None gdy date_of_birth nie jest ustawione."""
        profile = ProfileFactory(date_of_birth=None)
        serializer = ProfileSerializer(profile)
        data: Dict[str, Any] = dict(serializer.data)
        assert data["age"] is None

    def test_age_obliczany_gdy_data_urodzenia(self):
        """age powinien być obliczany gdy date_of_birth jest ustawione."""
        import datetime

        dob = datetime.date(1990, 1, 1)
        profile = ProfileFactory(date_of_birth=dob)
        serializer = ProfileSerializer(profile)
        data: Dict[str, Any] = dict(serializer.data)
        assert data["age"] is not None
        assert isinstance(data["age"], int)

    def test_email_jest_read_only(self):
        """Pole email powinno być tylko do odczytu."""
        profile = ProfileFactory()
        serializer = ProfileSerializer(
            profile,
            data={"email": "zmieniony@test.com", "first_name": "X"},
            partial=True,
        )
        assert serializer.is_valid()
        # email nie powinien zostać zmieniony przez walidację
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        assert "email" not in validated_data

    def test_role_jest_read_only(self):
        """Pole role powinno być tylko do odczytu."""
        profile = ProfileFactory()
        serializer = ProfileSerializer(
            profile,
            data={"role": "admin"},
            partial=True,
        )
        assert serializer.is_valid()
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        assert "role" not in validated_data

    def test_valid_partial_update(self):
        """Częściowa aktualizacja z poprawnym first_name powinna przejść walidację."""
        profile = ProfileFactory()
        serializer = ProfileSerializer(
            profile, data={"first_name": "Nowe"}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        validated_data = cast(Dict[str, Any], serializer.validated_data)
        assert validated_data["first_name"] == "Nowe"
