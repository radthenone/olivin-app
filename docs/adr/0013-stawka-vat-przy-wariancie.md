# Stawka podatku przypisana do wariantu, ze zwolnieniem jako osobną flagą

Sklep sprzedaje biżuterię oraz złoto inwestycyjne — sztabki i monety. W Polsce
złoto inwestycyjne korzysta ze zwolnienia przedmiotowego o innej podstawie
prawnej niż sprzedaż biżuterii, więc katalog zawiera pozycje o różnym
traktowaniu podatkowym. Jedna stawka dla całego katalogu jest wykluczona.

Stawka jest przypisana do **wariantu**, nie do produktu, ponieważ wariant jest
jedyną rzeczą kupowalną i to on nosi własną cenę. Zwolnienie nie jest
reprezentowane jako stawka zerowa, lecz jako osobna flaga wraz z podstawą
prawną — stawka zerowa i zwolnienie to różne byty na fakturze i w ewidencji,
a sprowadzenie ich do tej samej liczby uniemożliwia poprawne raportowanie.

## Consequences

Faktura obejmująca jednocześnie biżuterię i złoto inwestycyjne rozdziela
pozycje na dwie grupy i wskazuje podstawę zwolnienia. Ewidencja sprzedaży
zwolnionej jest prowadzona osobno.

Decyzja na poziomie schematu bazy danych. Musi obowiązywać przed powstaniem
pierwszego modelu wariantu i pozycji zamówienia — dołożenie jej po wdrożeniu
oznacza migrację danych produkcyjnych i korekty faktur wstecz.

Słownik domeny (`CONTEXT.md`) opisywał wcześniej stawkę jako przypisaną do
produktu; definicja została doprowadzona do zgodności z tą decyzją.

Kwalifikacja konkretnego towaru jako złota inwestycyjnego pozostaje
rozstrzygnięciem księgowości, nie konfiguracją techniczną.
