from __future__ import annotations

"""
Warstwa serwisów nie istnieje w apps/accounts — logika biznesowa
siedzi w modelu Profile (właściwości full_name, age) i managerze CustomUserManager.
Ten plik testuje logikę domenową modelu Profile.
"""

import datetime

import pytest
from django.db import IntegrityError
from freezegun import freeze_time

from apps.accounts.models import Profile
from apps.accounts.models.roles_model import RoleChoices
from tests.factories.accounts import ProfileFactory, UserFactory


@pytest.mark.django_db
class TestProfileFullName:
    """Testy właściwości full_name modelu Profile."""

    def test_full_name_imie_i_nazwisko(self):
        """full_name powinien zwracać 'Imię Nazwisko'."""
        profile = ProfileFactory(first_name="Anna", last_name="Nowak")
        assert profile.full_name == "Anna Nowak"

    def test_full_name_tylko_imie(self):
        """full_name bez last_name powinien zwrócić samo imię."""
        profile = ProfileFactory(first_name="Anna", last_name="")
        assert profile.full_name == "Anna"

    def test_full_name_tylko_nazwisko(self):
        """full_name bez first_name powinien zwrócić samo nazwisko."""
        profile = ProfileFactory(first_name="", last_name="Nowak")
        assert profile.full_name == "Nowak"

    def test_full_name_pusty(self):
        """full_name gdy oba pola puste powinien zwrócić pusty string."""
        profile = ProfileFactory(first_name="", last_name="")
        assert profile.full_name == ""


@pytest.mark.django_db
class TestProfileAge:
    """Testy właściwości age modelu Profile."""

    def test_age_none_gdy_brak_daty(self):
        """age powinien wynosić None gdy date_of_birth jest None."""
        profile = ProfileFactory(date_of_birth=None)
        assert profile.age is None

    @freeze_time("2025-06-15")
    def test_age_poprawne_obliczenie(self):
        """age powinien poprawnie obliczać wiek po urodzinach w danym roku."""
        dob = datetime.date(1990, 1, 1)
        profile = ProfileFactory(date_of_birth=dob)
        assert profile.age == 35

    @freeze_time("2025-06-15")
    def test_age_przed_urodzinami_w_tym_roku(self):
        """age powinien zwracać o 1 mniej gdy urodziny jeszcze nie minęły."""
        dob = datetime.date(1990, 12, 31)
        profile = ProfileFactory(date_of_birth=dob)
        assert profile.age == 34

    @freeze_time("2025-06-15")
    def test_age_w_dzien_urodzin(self):
        """age w dniu urodzin powinien być poprawny."""
        dob = datetime.date(1990, 6, 15)
        profile = ProfileFactory(date_of_birth=dob)
        assert profile.age == 35


@pytest.mark.django_db
class TestProfileStr:
    """Testy __str__ modelu Profile."""

    def test_str_format(self):
        """__str__ powinien zwracać 'email - rola'."""
        user = UserFactory(email="jan@test.com")
        profile = ProfileFactory(user=user)
        assert str(profile) == f"jan@test.com - {profile.role}"


@pytest.mark.django_db
class TestProfileOneToOne:
    """Testy relacji OneToOne Profile → CustomUser."""

    def test_jeden_user_jeden_profil(self):
        """Drugi profil dla tego samego użytkownika powinien rzucić IntegrityError."""
        user = UserFactory()
        ProfileFactory(user=user)
        with pytest.raises(IntegrityError):
            Profile.objects.create(user=user, role=RoleChoices.CUSTOMER)

    def test_profile_usuwany_z_userem(self):
        """Profil powinien być usuwany kaskadowo gdy user zostaje usunięty."""
        user = UserFactory()
        ProfileFactory(user=user)
        profile_id = user.profile.pk
        user.delete()
        assert not Profile.objects.filter(pk=profile_id).exists()
