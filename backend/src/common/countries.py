"""Fakty prawne o krajach wspólne dla aplikacji (bez zależności od Django)."""

# Kraje Unii poza Polską. Lista jest tu, a nie w bazie, bo zmienia się raz na
# dekadę i jest faktem prawnym, a nie danymi sklepu (ADR 0019).
EU_COUNTRIES = frozenset(
    {
        "AT",
        "BE",
        "BG",
        "CY",
        "CZ",
        "DE",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GR",
        "HR",
        "HU",
        "IE",
        "IT",
        "LT",
        "LU",
        "LV",
        "MT",
        "NL",
        "PT",
        "RO",
        "SE",
        "SI",
        "SK",
    }
)
