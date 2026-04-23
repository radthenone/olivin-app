from __future__ import annotations

import pytest
from django.db import IntegrityError

from apps.accounts.models import CustomUser
from tests.factories.accounts import UserFactory


@pytest.mark.django_db
class TestCustomUserManager:
    """Testy CustomUserManager — create_user i create_superuser."""

    def test_create_user_wymaga_emaila(self):
        """create_user bez emaila powinien rzucić ValueError."""
        with pytest.raises(ValueError, match="Email jest wymagany"):
            CustomUser.objects.create_user(email="", password="pass")

    def test_create_user_normalizuje_email(self):
        """Email powinien być znormalizowany (małe litery domeny)."""
        user = CustomUser.objects.create_user(
            email="Test@EXAMPLE.COM", password="pass123"
        )
        assert user.email == "Test@example.com"

    def test_create_user_ustawia_haslo(self):
        """Hasło powinno być zhashowane, nie przechowywane w plaintext."""
        user = CustomUser.objects.create_user(email="a@test.com", password="secret")
        assert user.check_password("secret")
        assert user.password != "secret"

    def test_create_user_domyslne_flagi(self):
        """Zwykły użytkownik nie jest adminem ani superuserem."""
        user = CustomUser.objects.create_user(email="b@test.com", password="pass123")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser_ustawia_flagi(self):
        """Superuser musi mieć is_staff=True i is_superuser=True."""
        su = CustomUser.objects.create_superuser(
            email="su@test.com", password="superpass"
        )
        assert su.is_staff is True
        assert su.is_superuser is True

    def test_create_superuser_wymaga_is_staff(self):
        """create_superuser z is_staff=False powinien rzucić ValueError."""
        with pytest.raises(ValueError, match="is_staff"):
            CustomUser.objects.create_superuser(
                email="bad@test.com", password="pass", is_staff=False
            )

    def test_create_superuser_wymaga_is_superuser(self):
        """create_superuser z is_superuser=False powinien rzucić ValueError."""
        with pytest.raises(ValueError, match="is_superuser"):
            CustomUser.objects.create_superuser(
                email="bad2@test.com", password="pass", is_superuser=False
            )


@pytest.mark.django_db
class TestCustomUserModel:
    """Testy modelu CustomUser."""

    def test_str_zwraca_email(self):
        """__str__ powinien zwracać email użytkownika."""
        user = UserFactory(email="jan@test.com")
        assert str(user) == "jan@test.com"

    def test_full_name_z_imieniem_i_nazwiskiem(self):
        """full_name powinien zwracać imię i nazwisko."""
        user = UserFactory.build(first_name="Jan", last_name="Kowalski")
        assert user.full_name == "Jan Kowalski"

    def test_full_name_bez_nazwiska(self):
        """full_name bez last_name powinien zwrócić samo imię (bez spacji)."""
        user = UserFactory.build(first_name="Jan", last_name="")
        assert user.full_name == "Jan"

    def test_full_name_pusty(self):
        """full_name gdy oba pola puste powinien zwrócić pusty string."""
        user = UserFactory.build(first_name="", last_name="")
        assert user.full_name == ""

    def test_email_jest_unikalny(self, db):
        """Dwie próby stworzenia użytkownika z tym samym emailem powinny rzucić błąd."""
        UserFactory(email="dup@test.com")
        with pytest.raises(IntegrityError):
            CustomUser.objects.create_user(email="dup@test.com", password="pass")

    def test_username_moze_byc_null(self, db):
        """Wiele użytkowników może mieć username=None (NULL nie łamie UNIQUE)."""
        u1 = UserFactory(username=None)
        u2 = UserFactory(username=None)
        assert u1.username is None
        assert u2.username is None

    def test_username_unikalny_gdy_podany(self, db):
        """Dwóch użytkowników z tym samym username powinno rzucić IntegrityError."""
        UserFactory(username="jankowalski")
        with pytest.raises(IntegrityError):
            CustomUser.objects.create_user(
                email="other@test.com", password="pass", username="jankowalski"
            )

    def test_inactive_user(self, db):
        """Użytkownik z is_active=False powinien być poprawnie tworzony."""
        user = UserFactory(is_active=False)
        assert user.is_active is False

    def test_username_field_to_email(self):
        """USERNAME_FIELD powinien wskazywać na 'email'."""
        assert CustomUser.USERNAME_FIELD == "email"

    def test_required_fields_puste(self):
        """REQUIRED_FIELDS poza emailem powinno być puste."""
        assert CustomUser.REQUIRED_FIELDS == []
