"""Zamknięte listy wartości cech katalogu.

Cechy produktu i wariantu są wyborem z listy, nie wolną etykietą
(`CONTEXT.md`, ProductVariant). Wolny tekst uniemożliwiłby filtrowanie
listy produktów — dwa zapisy tej samej wartości rozjeżdżają filtr.
"""

from django.db import models


class ProductStatus(models.TextChoices):
    DRAFT = "draft", "Szkic"
    PUBLISHED = "published", "Opublikowany"


class Material(models.TextChoices):
    """Kruszec, z którego wykonany jest wyrób."""

    GOLD = "gold", "Złoto"
    SILVER = "silver", "Srebro"
    PLATINUM = "platinum", "Platyna"
    PALLADIUM = "palladium", "Pallad"


class Fineness(models.TextChoices):
    """Próba kruszcu — zawartość czystego metalu w tysięcznych."""

    F333 = "333", "333 (8 karatów)"
    F375 = "375", "375 (9 karatów)"
    F585 = "585", "585 (14 karatów)"
    F750 = "750", "750 (18 karatów)"
    F916 = "916", "916 (22 karaty)"
    F925 = "925", "925 (srebro próby 925)"
    F950 = "950", "950 (platyna)"
    F999 = "999", "999 (kruszec inwestycyjny)"


class MetalColor(models.TextChoices):
    YELLOW = "yellow", "Żółte"
    WHITE = "white", "Białe"
    ROSE = "rose", "Różowe"
    BICOLOR = "bicolor", "Dwukolorowe"


class Stone(models.TextChoices):
    """Rodzaj kamienia widoczny jako cecha wariantu.

    Parametry konkretnego kamienia — masa, czystość, certyfikat — należą do
    osobnego modelu (`CONTEXT.md`, Gemstone), nie do tej listy.
    """

    DIAMOND = "diamond", "Diament"
    SAPPHIRE = "sapphire", "Szafir"
    RUBY = "ruby", "Rubin"
    EMERALD = "emerald", "Szmaragd"
    PEARL = "pearl", "Perła"
    AMBER = "amber", "Bursztyn"
    TOPAZ = "topaz", "Topaz"
    AMETHYST = "amethyst", "Ametyst"
    CUBIC_ZIRCONIA = "cubic_zirconia", "Cyrkonia"
    MOISSANITE = "moissanite", "Moissanit"


class RingSize(models.TextChoices):
    """Rozmiary pierścionków w skali używanej w Polsce (obwód w milimetrach)."""

    S8 = "8", "8"
    S9 = "9", "9"
    S10 = "10", "10"
    S11 = "11", "11"
    S12 = "12", "12"
    S13 = "13", "13"
    S14 = "14", "14"
    S15 = "15", "15"
    S16 = "16", "16"
    S17 = "17", "17"
    S18 = "18", "18"
    S19 = "19", "19"
    S20 = "20", "20"
    S21 = "21", "21"
    S22 = "22", "22"
    S23 = "23", "23"
    S24 = "24", "24"
    S25 = "25", "25"
    S26 = "26", "26"


class Length(models.TextChoices):
    """Długości łańcuszków i bransolet w centymetrach."""

    L16 = "16", "16 cm"
    L18 = "18", "18 cm"
    L20 = "20", "20 cm"
    L36 = "36", "36 cm"
    L38 = "38", "38 cm"
    L40 = "40", "40 cm"
    L42 = "42", "42 cm"
    L45 = "45", "45 cm"
    L50 = "50", "50 cm"
    L55 = "55", "55 cm"
    L60 = "60", "60 cm"
    L70 = "70", "70 cm"
    L80 = "80", "80 cm"
