"""Przygotowanie zdjęć katalogu: kadr, skalowanie, WebP (ADR 0025)."""

from __future__ import annotations

import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image

from apps.products.models.image import (
    RENDITION_WIDTHS,
    WEBP_QUALITY,
    ImageStatus,
    ProductImage,
)
from core.storage.storages import ProductStorage


def rendition_key(image: ProductImage, token: str, width: int) -> str:
    """`products/<id>/<uuid>-<rozmiar>.webp` — klucz bez hosta i bez bucketa."""
    return f"products/{image.pk}/{token}-{width}.webp"


def apply_crop(source: Image.Image, crop: dict | None) -> Image.Image:
    """Wycina prostokąt kadru; pusty kadr zostawia całe zdjęcie.

    Prostokąt jest przycinany do granic zdjęcia, bo kadr przychodzi z klienta
    i nie ma powodu ufać, że mieści się w oryginale.
    """
    if not crop:
        return source
    left = min(crop["x"], source.width)
    top = min(crop["y"], source.height)
    right = min(left + crop["width"], source.width)
    bottom = min(top + crop["height"], source.height)
    if right <= left or bottom <= top:
        return source
    return source.crop((left, top, right, bottom))


def scale_to_width(source: Image.Image, width: int) -> Image.Image:
    """Skaluje do zadanej szerokości, ale nigdy w górę.

    Powiększanie nie dokłada szczegółu, a waży swoje — zdjęcie węższe niż
    rozmiar docelowy zostaje w swojej szerokości. Klucz i tak powstaje, więc
    kontrakt API się nie zmienia.
    """
    if source.width <= width:
        return source.copy()
    height = max(1, round(source.height * width / source.width))
    return source.resize((width, height), Image.Resampling.LANCZOS)


def render_renditions(image: ProductImage) -> int:
    """Zapisuje wszystkie rozmiary i oznacza zdjęcie jako gotowe."""
    storage = ProductStorage()
    token = uuid.uuid4().hex

    with image.original.open("rb") as handle:
        source = Image.open(handle)
        source.load()

    # WebP nie zna palety ani trybu CMYK — bez konwersji zapis pada albo
    # gubi kolory.
    if source.mode not in ("RGB", "RGBA"):
        source = source.convert("RGBA" if "A" in source.getbands() else "RGB")

    cropped = apply_crop(source, image.crop)

    renditions: dict[str, str] = {}
    for width in RENDITION_WIDTHS:
        buffer = BytesIO()
        scale_to_width(cropped, width).save(
            buffer, format="WEBP", quality=WEBP_QUALITY, method=6
        )
        key = rendition_key(image, token, width)
        storage.save(key, ContentFile(buffer.getvalue()))
        renditions[str(width)] = key

    ProductImage.objects.filter(pk=image.pk).update(
        renditions=renditions, status=ImageStatus.READY
    )
    return len(renditions)
