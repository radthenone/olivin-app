# Grawer jako opcjonalna pozycja ceny wyłączająca prawo odstąpienia

Sklep przyjmuje zamówienia z grawerunkiem. Nie każdy produkt może być
grawerowany, więc możliwość ta jest flagą na produkcie, a nie założeniem
obowiązującym cały katalog.

Grawer jest wyceniany **osobną pozycją** doliczaną do ceny wariantu, nie
wliczaną w nią. Dzięki temu na zamówieniu i na dokumencie sprzedaży widać, za co
klient zapłacił, a zmiana cennika grawerunku nie wymaga przeceniania wariantów.

## Consequences

Pozycja koszyka i pozycja zamówienia przechowują parametry personalizacji —
treść grawerunku — obok wariantu i ilości. Sama para wariant plus ilość
przestaje jednoznacznie identyfikować pozycję: dwie pozycje na ten sam wariant
z różnym grawerunkiem to dwie różne pozycje, których nie wolno scalić.

Magazyn musi odróżniać egzemplarz magazynowy od wykonywanego na zamówienie.
Rezerwacja stanu dla wyrobu grawerowanego działa inaczej niż dla towaru z półki,
ponieważ egzemplarz po wykonaniu grawerunku przestaje być zamienny.

Wyrób z grawerunkiem jest towarem zindywidualizowanym, więc jest wyłączony spod
ustawowego prawa odstąpienia. W praktyce oznacza to, że przy takich zamówieniach
obowiązek zwrotu pieniędzy nie powstaje, a kupon pozostaje swobodną decyzją
sklepu — to jedyny przypadek, w którym rekompensata wyłącznie kuponowa nie
wchodzi w kolizję z ustawą. Zasady ogólne opisuje
[ADR 0015](0015-podstawa-zwrotu-decyduje-o-formie-rekompensaty.md).

Wyłączenie nie obejmuje wad towaru — wadliwy wyrób grawerowany podlega
reklamacji na zasadach ogólnych.

Regulamin musi informować o wyłączeniu prawa odstąpienia **przed** złożeniem
zamówienia z grawerunkiem, a nie dopiero przy zwrocie.
