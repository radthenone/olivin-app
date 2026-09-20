from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from apps.products.models.metal_rate import MetalRate, MetalRateStatus
from apps.products.services.pricing import recalculate_prices
from core.integrations.metal_rate import get_provider


@shared_task
def recalculate_variant_prices(metal: str, fineness: str) -> int:
    """Przelicza ceny wariantów po zatwierdzeniu kursu (ADR 0022)."""
    return recalculate_prices(metal, fineness)


@shared_task
def notify_owner_about_rate_activation(
    rate_id: str, previous_rate_id: str | None = None
) -> bool:
    """Wiadomość do właściciela po każdej aktywacji kursu.

    Aktywacja przecenia cały katalog danego kruszcu, więc zostaje po niej
    ślad poza dziennikiem panelu: kto zatwierdził, co było wcześniej i co
    obowiązuje teraz.
    """
    rate = MetalRate.objects.filter(pk=rate_id).select_related("activated_by").first()
    if rate is None:
        return False

    previous = MetalRate.objects.filter(pk=previous_rate_id).first()
    previous_line = (
        f"Poprzedni kurs: {previous.price} za gram (z {previous.quoted_on})."
        if previous is not None
        else "Poprzedniego kursu nie było — to pierwszy kurs dla tej próby."
    )
    who = getattr(rate.activated_by, "email", None) or "nieznany użytkownik"

    send_mail(
        subject=(f"Aktywowano kurs: {rate.get_metal_display()} próba {rate.fineness}"),
        message=(
            f"{previous_line}\n"
            f"Nowy kurs: {rate.price} za gram (z {rate.quoted_on}, "
            f"źródło: {rate.source}).\n"
            f"Aktywował: {who}.\n\n"
            "Ceny wariantów z tego kruszcu i próby zostały przeliczone. "
            "Ceny ręczne pozostały bez zmian."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.SHOP_OWNER_EMAIL],
        fail_silently=False,
    )
    return True


@shared_task
def propose_metal_rates() -> int:
    """Raz w miesiącu wstawia notowania jako `proposed` (ADR 0022, ADR 0027).

    Propozycja niczego nie zmienia — ceny przelicza dopiero aktywacja przez
    właściciela. Notowanie identyczne z obowiązującym jest pomijane, żeby
    panel nie zapełniał się propozycjami bez treści.
    """
    created = 0
    for quote in get_provider().quotes():
        active = MetalRate.objects.active_for(quote.metal, quote.fineness)
        if active is not None and active.price_per_gram == quote.price_per_gram:
            continue
        already_proposed = MetalRate.objects.filter(
            metal=quote.metal,
            fineness=quote.fineness,
            status=MetalRateStatus.PROPOSED,
            quoted_on=quote.quoted_on,
            price_per_gram=quote.price_per_gram,
        ).exists()
        if already_proposed:
            continue
        MetalRate.objects.create(
            metal=quote.metal,
            fineness=quote.fineness,
            price_per_gram=quote.price_per_gram,
            currency=quote.currency,
            quoted_on=quote.quoted_on,
            source=quote.source,
            status=MetalRateStatus.PROPOSED,
        )
        created += 1
    return created


@shared_task
def render_product_image(image_id: str) -> int:
    """Tnie oryginał do kadru i zapisuje trzy rozmiary WebP (ADR 0025).

    Oryginał zostaje nietknięty w prywatnym buckecie, więc zmiana kadru
    uruchamia to samo zadanie bez ponownego wgrywania. Dopiero gdy wszystkie
    rozmiary są zapisane, zdjęcie przechodzi w `ready` i pojawia się w API.
    """
    from apps.products.images import render_renditions
    from apps.products.models.image import ProductImage

    image = ProductImage.objects.filter(pk=image_id).first()
    if image is None:
        return 0
    return render_renditions(image)
