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

    def test_newest_effective_version_is_current(self):
        """Najnowsza obowiązująca wersja jest bieżąca."""
        ConsentDocumentFactory(
            version="2026-01", effective_from=datetime.date(2026, 1, 1)
        )
        newer = ConsentDocumentFactory(
            version="2026-06", effective_from=datetime.date(2026, 6, 1)
        )

        assert ConsentDocument.objects.current(ConsentKind.TERMS) == newer

    def test_future_version_is_not_effective_yet(self):
        """Wersja z przyszłości jeszcze nie obowiązuje."""
        current = ConsentDocumentFactory(
            version="2026-01", effective_from=datetime.date(2026, 1, 1)
        )
        ConsentDocumentFactory(
            version="2099-01", effective_from=datetime.date(2099, 1, 1)
        )

        assert ConsentDocument.objects.current(ConsentKind.TERMS) == current

    def test_kind_without_document_has_no_current_version(self):
        """Rodzaj bez dokumentu nie ma bieżącej wersji."""
        assert ConsentDocument.objects.current(ConsentKind.MARKETING) is None

    def test_version_is_unique_within_kind(self):
        """Wersja jest unikalna w obrębie rodzaju."""
        ConsentDocumentFactory(kind=ConsentKind.TERMS, version="2026-01")

        with pytest.raises(IntegrityError):
            ConsentDocumentFactory(kind=ConsentKind.TERMS, version="2026-01")


@pytest.mark.django_db
class TestConsentInvalidation:
    """Nowa wersja dokumentu unieważnia wcześniejszą zgodę (`CONTEXT.md`, Consent)."""

    def test_consent_to_current_version_is_valid(self):
        """Zgoda na bieżącą wersję jest aktualna."""
        consent = ConsentFactory()

        assert Consent.objects.has_current_consent(ConsentKind.TERMS, user=consent.user)

    def test_new_version_invalidates_consent(self):
        """Nowa wersja unieważnia zgodę."""
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

    def test_consent_to_new_version_restores_validity(self):
        """Ponowna zgoda na nową wersję przywraca aktualność."""
        consent = ConsentFactory(
            document__version="2026-01",
            document__effective_from=datetime.date(2026, 1, 1),
        )
        newer = ConsentDocumentFactory(
            version="2026-06", effective_from=datetime.date(2026, 6, 1)
        )
        ConsentFactory(user=consent.user, document=newer)

        assert Consent.objects.has_current_consent(ConsentKind.TERMS, user=consent.user)

    def test_consent_to_other_kind_does_not_count(self):
        """Zgoda na inny rodzaj dokumentu się nie liczy."""
        consent = ConsentFactory(document__kind=ConsentKind.PRIVACY)
        ConsentDocumentFactory(kind=ConsentKind.MARKETING)

        assert not Consent.objects.has_current_consent(
            ConsentKind.MARKETING, user=consent.user
        )

    def test_missing_document_means_no_consent(self):
        """Brak dokumentu oznacza brak zgody."""
        user = UserFactory()

        assert not Consent.objects.has_current_consent(ConsentKind.TERMS, user=user)

    def test_consent_remembers_version_at_grant_time(self):
        """Zgoda zapamiętuje wersję z chwili udzielenia."""
        consent = ConsentFactory(document__version="2026-01")

        assert consent.version == "2026-01"
        assert consent.granted_at is not None


@pytest.mark.django_db
class TestGuestConsent:
    """Gość nie ma konta — identyfikuje go e-mail podany w kasie."""

    def test_guest_consents_by_email(self):
        """Gość udziela zgody po adresie e-mail."""
        consent = GuestConsentFactory(email="anna@example.com")

        assert Consent.objects.has_current_consent(
            ConsentKind.TERMS, email="anna@example.com"
        )
        assert consent.user is None

    def test_guest_email_is_case_insensitive(self):
        """E-mail gościa nie rozróżnia wielkości liter."""
        GuestConsentFactory(email="Anna@Example.com")

        assert Consent.objects.has_current_consent(
            ConsentKind.TERMS, email="anna@example.com"
        )

    def test_guest_consent_does_not_count_for_account(self):
        """Zgoda gościa nie liczy się dla konta."""
        GuestConsentFactory(email="anna@example.com")
        user = UserFactory(email="anna@example.com")

        assert not Consent.objects.has_current_consent(ConsentKind.TERMS, user=user)


@pytest.mark.django_db
class TestSubjectIsUserXorEmail:
    """Zgoda należy do użytkownika albo do e-maila gościa — dokładnie jednego."""

    def test_user_and_email_together_are_rejected(self):
        """Użytkownik i e-mail naraz są odrzucani."""
        with pytest.raises(ValidationError) as error:
            ConsentFactory(email="anna@example.com")

        assert "email" in error.value.message_dict

    def test_missing_both_is_rejected(self):
        """Brak użytkownika i e-maila jest odrzucany."""
        with pytest.raises(ValidationError) as error:
            ConsentFactory(user=None, email="")

        assert "email" in error.value.message_dict

    def test_database_rejects_inconsistency_too(self):
        """Baza też nie przepuści niespójności."""
        document = ConsentDocumentFactory()
        user = UserFactory()

        with pytest.raises(IntegrityError):
            Consent.objects.bulk_create(
                [Consent(user=user, email="anna@example.com", document=document)]
            )

    def test_empty_subject_is_rejected_by_database(self):
        """Pusty podmiot nie przechodzi w bazie."""
        document = ConsentDocumentFactory()

        with pytest.raises(IntegrityError):
            Consent.objects.bulk_create(
                [Consent(user=None, email="", document=document)]
            )


@pytest.mark.django_db
class TestPendingConsents:
    """Zaległe zgody: bieżące wersje wymaganych dokumentów bez akceptacji klienta."""

    def test_account_without_consents_has_terms_and_privacy_pending(self):
        """Konto sprzed #207 bez zgód widzi regulamin i politykę jako zaległe."""
        for kind in ConsentKind.values:
            ConsentDocumentFactory(kind=kind)
        user = UserFactory()

        pending = ConsentDocument.objects.pending_for(user)

        assert [d.kind for d in pending] == ["terms", "privacy"]

    def test_new_version_makes_accepted_document_pending(self):
        """Nowa obowiązująca wersja regulaminu → regulamin znów zaległy."""
        old = ConsentDocumentFactory(effective_from=datetime.date(2026, 1, 1))
        privacy = ConsentDocumentFactory(kind=ConsentKind.PRIVACY)
        user = UserFactory()
        ConsentFactory(user=user, document=old)
        ConsentFactory(user=user, document=privacy)
        new = ConsentDocumentFactory(effective_from=datetime.date(2026, 6, 1))

        assert ConsentDocument.objects.pending_for(user) == [new]

    def test_future_version_is_not_pending_yet(self):
        """Wersja, która jeszcze nie obowiązuje, nie jest zaległa."""
        terms = ConsentDocumentFactory()
        user = UserFactory()
        ConsentFactory(user=user, document=terms)
        ConsentDocumentFactory(
            effective_from=datetime.date.today() + datetime.timedelta(days=1)
        )

        assert ConsentDocument.objects.pending_for(user) == []
