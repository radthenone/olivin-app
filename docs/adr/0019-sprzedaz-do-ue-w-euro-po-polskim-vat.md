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

## Uzupełnienie (2026-09-19)

Ceny źródłowe są w złotych. Kurs euro pochodzi z Narodowego Banku Polskiego,
pobierany codziennie; klient z kraju Unii widzi euro w katalogu i w kasie,
płaci w euro, a kurs z chwili złożenia zamówienia zostaje w nim zapisany.

## Uzupełnienie (2026-09-22)

Kurs euro jest odświeżany **co 30 dni**, nie codziennie — sklep jubilerski
nie potrzebuje kursu z dnia, a stała cena przez miesiąc jest czytelniejsza dla
klienta i nie zmienia kwot w koszyku między wizytami. Nowy kurs działa
**automatycznie**, bez ręcznej aktywacji przez właściciela; to celowa różnica
wobec cyklu życia kursu kruszcu z
[ADR 0022](0022-cena-skladnikowa-z-przeliczeniem-po-zatwierdzeniu-kursu.md),
bo kurs waluty nie zmienia marży, tylko sposób zapisu tej samej ceny.

Cena w euro po przeliczeniu jest zaokrąglana **w górę do końcówki ,00 albo
,50**, żeby katalog nie pokazywał kwot w rodzaju 137,83 €. Zaokrąglenie nigdy
nie obniża ceny poniżej kosztu wariantu przeliczonego tym samym kursem —
próg z ADR 0022 obowiązuje w każdej walucie.
