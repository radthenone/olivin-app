"""Które pola katalogu podlegają tłumaczeniu.

Jedno miejsce zamiast rozsypanych deklaracji na modelach: zadanie w tle,
panel i warstwa serializacji muszą czytać tę samą listę, inaczej tłumaczy
się co innego, niż się pokazuje.

Slug nie jest tłumaczony — jest jeden, angielski i niezmienny po publikacji
(`CONTEXT.md`, Translation).
"""

from __future__ import annotations

from django.apps import apps

TRANSLATABLE_FIELDS: dict[str, tuple[str, ...]] = {
    "products.Product": ("name", "description"),
    "products.ProductImage": ("alt_text",),
    "categories.Category": ("name",),
    "collections.Collection": ("name",),
}


def fields_for(obj) -> tuple[str, ...]:
    label = f"{obj._meta.app_label}.{obj._meta.object_name}"
    return TRANSLATABLE_FIELDS.get(label, ())


def translatable_models() -> list[type]:
    return [apps.get_model(label) for label in TRANSLATABLE_FIELDS]
