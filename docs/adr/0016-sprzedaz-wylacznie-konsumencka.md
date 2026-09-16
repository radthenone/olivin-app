# Sprzedaż wyłącznie konsumencka, bez integracji z KSeF

Sklep prowadzi sprzedaż wyłącznie konsumencką, dokumentowaną paragonem. Nie
wystawia faktur dla firm, co stawia Krajowy System e-Faktur poza zakresem
projektu.

Decyzja jest podyktowana kosztem. Integracja z KSeF oznacza obsługę interfejsu
programistycznego, autoryzację, obsługę błędów oraz przechowywanie
urzędowych poświadczeń odbioru — nakład nieuzasadniony na etapie przed
uruchomieniem sprzedaży, gdy nie ma odbiorców biznesowych.

## Consequences

Moduł zamówień i płatności nie zawiera warstwy fakturowania dla firm, co
znacząco zawęża jego zakres.

Decyzja jest odwracalna, ale nie za darmo: wejście w sprzedaż firmom oznacza
dołożenie fakturowania, integracji z KSeF i innych zasad zwrotów, ponieważ
ochrona konsumencka opisana w [ADR 0015](0015-podstawa-zwrotu-decyduje-o-formie-rekompensaty.md)
nie obejmuje transakcji między przedsiębiorcami. Temat pozostaje odnotowany
na trackerze jako pomysł na przyszłość.

Obowiązujące terminy i zakres KSeF zmieniały się wielokrotnie. Przed
ewentualnym wejściem w sprzedaż firmom stan przepisów wymaga potwierdzenia
u księgowości — nie należy opierać się na tym dokumencie.
