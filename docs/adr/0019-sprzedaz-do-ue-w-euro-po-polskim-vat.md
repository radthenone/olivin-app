# Sprzedaż do Unii Europejskiej w euro, rozliczana polskim podatkiem

Sklep sprzedaje w Polsce oraz do pozostałych krajów Unii Europejskiej. Ceny dla
Polski są wyrażone w złotych, ceny dla Unii w euro i powstają z przeliczenia cen
złotowych. Sprzedaż jest rozliczana polskim podatkiem. Koszt wysyłki odpowiada
stawce właściwej dla kraju odbiorcy.

## Consequences

Cena w euro jest wynikiem przeliczenia, nie osobnym cennikiem utrzymywanym
ręcznie. Kurs przeliczenia i moment jego pobrania muszą być zapisane przy
zamówieniu, inaczej nie da się odtworzyć, dlaczego klient zapłacił daną kwotę.
Kwoty pozostają liczbami całkowitymi w najmniejszej jednostce waluty wraz
z kodem waluty, zgodnie z [ADR 0009](0009-kwoty-jako-liczby-calkowite.md) —
euro nie jest tu wyjątkiem.

Model podatku przewiduje **stawkę zależną od kraju odbiorcy**, mimo że dziś
wszędzie stosowana jest stawka polska. Powód jest konkretny: sprzedaż
konsumencka do Unii rozliczana stawką kraju sprzedawcy działa wyłącznie do progu
sprzedaży wysyłkowej, liczonego łącznie dla całej Unii. Po jego przekroczeniu
powstaje obowiązek rozliczania stawką kraju odbiorcy, w praktyce przez procedurę
OSS.

Gdyby stawka była w modelu pojedynczą wartością, przekroczenie progu oznaczałoby
migrację schematu w trakcie działania sprzedaży, pod presją terminu
podatkowego. Przy stawce per kraj jest to zmiana konfiguracji. Koszt dzisiaj to
jedno pole; koszt odwrócenia później to migracja danych produkcyjnych.

Sprzedaż wysyłkowa wymaga śledzenia obrotu wobec progu. Samo przekroczenie jest
zdarzeniem księgowym, nie technicznym — system ma dostarczyć dane, a nie
rozstrzygać o rejestracji w procedurze OSS.

Zastrzeżenie: zastosowanie polskiej stawki do sprzedaży konsumenckiej w Unii
wymaga potwierdzenia u księgowości wraz z bieżącym stanem obrotu wobec progu.
Ten dokument zapisuje decyzję właściciela i przygotowuje model na jej zmianę,
nie przesądza o kwalifikacji podatkowej.

Wielojęzyczność katalogu jest zagadnieniem odrębnym od wielowalutowości
i rozliczeń transgranicznych — katalog może być tłumaczony niezależnie od tego,
dokąd sklep sprzedaje.
