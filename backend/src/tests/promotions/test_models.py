"""Model promocji: kod, zakres wartości i usunięta aplikacja `discounts`."""

from __future__ import annotations

import pytest
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.promotions.models import PromotionKind
from core.paths import APPS_DIR, CORE_DIR
from tests.factories.promotions import PromotionFactory


class TestDiscountsAppRemoved:
    """`apps.discounts` ustąpiła `apps.promotions` („Unikaj: Discount")."""

    def test_not_installed(self):
        """Nie ma jej w zainstalowanych aplikacjach."""
        assert "apps.discounts" not in settings.INSTALLED_APPS
        assert not apps.is_installed("apps.discounts")

    def test_no_code_left(self):
        """Na dysku nie ma po niej kodu."""
        assert not list((APPS_DIR / "discounts").glob("**/*.py"))

    def test_settings_and_urls_do_not_mention_it(self):
        """Ustawienia i routing nie odwołują się do usuniętej aplikacji."""
        for path in (
            CORE_DIR / "settings" / "components" / "apps.py",
            CORE_DIR / "urls.py",
        ):
            assert "discounts" not in path.read_text(encoding="utf-8")


@pytest.mark.django_db
class TestPromotionModel:
    """Walidacja promocji w panelu."""

    def test_code_is_stored_uppercase(self):
        """Kod jest zapisywany wielkimi literami, bez spacji wokół."""
        assert PromotionFactory(code="  lato ").code == "LATO"

    def test_percent_above_hundred_is_rejected(self):
        """Obniżka powyżej 100% nie ma sensu."""
        promotion = PromotionFactory.build(kind=PromotionKind.PERCENT, value=120)

        with pytest.raises(ValidationError):
            promotion.full_clean()

    def test_amount_above_hundred_is_fine(self):
        """Kwota 150 zł to 15000 groszy — limit 100 dotyczy tylko procentu."""
        promotion = PromotionFactory.build(kind=PromotionKind.AMOUNT, value=15000)

        promotion.full_clean()
