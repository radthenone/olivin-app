from __future__ import annotations

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from apps.consents.models import Consent, ConsentDocument, ConsentKind
from tests.factories.accounts import UserFactory
from tests.factories.consents import (
    ConsentDocumentFactory,
    ConsentFactory,
    GuestConsentFactory,
)


@pytest.mark.django_db
class TestCurrentDocument:
    """Bieżąca wersja to najnowsza, która już obowiązuje — nie najnowsza w ogóle."""

    def test_najnowsza_obowiazujaca_wersja_jest_biezaca(self):
        ConsentDocumentFactory(
            version="2026-01", effective_from=datetime.date(2026, 1, 1)
        )
        newer = ConsentDocumentFactory(
            version="2026-06", effective_from=datetime.date(2026, 6, 1)
        )

        assert ConsentDocument.objects.current(ConsentKind.TERMS) == newer

    def test_wersja_z_przyszlosci_jeszcze_nie_obowiazuje(self):
        current = ConsentDocumentFactory(
            version="2026-01", effective_from=datetime.date(2026, 1, 1)
        )
        ConsentDocumentFactory(
            version="2099-01", effective_from=datetime.date(2099, 1, 1)
        )

        assert ConsentDocument.objects.current(ConsentKind.TERMS) == current

    def test_rodzaj_bez_dokumentu_nie_ma_biezacej_wersji(self):
        assert ConsentDocument.objects.current(ConsentKind.MARKETING) is None

    def test_wersja_jest_unikalna_w_obrebie_rodzaju(self):
        ConsentDocumentFactory(kind=ConsentKind.TERMS, version="2026-01")

        with pytest.raises(IntegrityError):
            ConsentDocumentFactory(kind=ConsentKind.TERMS, version="2026-01")


@pytest.mark.django_db
class TestConsentInvalidation:
    """Nowa wersja dokumentu unieważnia wcześniejszą zgodę (`CONTEXT.md`, Consent)."""

    def test_zgoda_na_biezaca_wersje_jest_aktualna(self):
        consent = ConsentFactory()

        assert Consent.objects.has_current_consent(ConsentKind.TERMS, user=consent.user)

    def test_nowa_wersja_uniewaznia_zgode(self):
        consent = ConsentFactory(
            document__version="2026-01",
            document__effective_from=datetime.date(2026, 1, 1),
        )
        ConsentDocumentFactory(
            version="2026-06", effective_from=datetime.date(2026, 6, 1)
        )

        assert not Consent.objects.has_current_consent(
            ConsentKind.TERMS, user=consent.user
        )

    def test_ponowna_zgoda_na_nowa_wersje_przywraca_aktualnosc(self):
        consent = ConsentFactory(
            document__version="2026-01",
            document__effective_from=datetime.date(2026, 1, 1),
        )
        newer = ConsentDocumentFactory(
            version="2026-06", effective_from=datetime.date(2026, 6, 1)
        )
        ConsentFactory(user=consent.user, document=newer)

        assert Consent.objects.has_current_consent(ConsentKind.TERMS, user=consent.user)

    def test_zgoda_na_inny_rodzaj_nie_liczy_sie(self):
        consent = ConsentFactory(document__kind=ConsentKind.PRIVACY)
        ConsentDocumentFactory(kind=ConsentKind.MARKETING)

        assert not Consent.objects.has_current_consent(
            ConsentKind.MARKETING, user=consent.user
        )

    def test_brak_dokumentu_oznacza_brak_zgody(self):
        user = UserFactory()

        assert not Consent.objects.has_current_consent(ConsentKind.TERMS, user=user)

    def test_zgoda_zapamietuje_wersje_z_chwili_udzielenia(self):
        consent = ConsentFactory(document__version="2026-01")

        assert consent.version == "2026-01"
        assert consent.granted_at is not None


@pytest.mark.django_db
class TestGuestConsent:
    """Gość nie ma konta — identyfikuje go e-mail podany w kasie."""

    def test_gosc_udziela_zgody_po_emailu(self):
        consent = GuestConsentFactory(email="anna@example.com")

        assert Consent.objects.has_current_consent(
            ConsentKind.TERMS, email="anna@example.com"
        )
        assert consent.user is None

    def test_email_goscia_nie_rozroznia_wielkosci_liter(self):
        GuestConsentFactory(email="Anna@Example.com")

        assert Consent.objects.has_current_consent(
            ConsentKind.TERMS, email="anna@example.com"
        )

    def test_zgoda_goscia_nie_liczy_sie_dla_konta(self):
        GuestConsentFactory(email="anna@example.com")
        user = UserFactory(email="anna@example.com")

        assert not Consent.objects.has_current_consent(ConsentKind.TERMS, user=user)


@pytest.mark.django_db
class TestSubjectIsUserXorEmail:
    """Zgoda należy do użytkownika albo do e-maila gościa — dokładnie jednego."""

    def test_uzytkownik_i_email_naraz_sa_odrzucone(self):
        with pytest.raises(ValidationError) as error:
            ConsentFactory(email="anna@example.com")

        assert "email" in error.value.message_dict

    def test_brak_obu_jest_odrzucony(self):
        with pytest.raises(ValidationError) as error:
            ConsentFactory(user=None, email="")

        assert "email" in error.value.message_dict

    def test_baza_tez_nie_przepusci_niespojnosci(self):
        document = ConsentDocumentFactory()
        user = UserFactory()

        with pytest.raises(IntegrityError):
            Consent.objects.bulk_create(
                [Consent(user=user, email="anna@example.com", document=document)]
            )

    def test_pusty_podmiot_nie_przechodzi_w_bazie(self):
        document = ConsentDocumentFactory()

        with pytest.raises(IntegrityError):
            Consent.objects.bulk_create(
                [Consent(user=None, email="", document=document)]
            )
