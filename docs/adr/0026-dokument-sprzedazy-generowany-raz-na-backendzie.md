# Dokument sprzedaży powstaje raz, na backendzie, z ciągłą numeracją

Potwierdzenie zamówienia (zawsze), faktura imienna dla konsumenta (gdy poda
dane) i korekta (przy przyjętym zwrocie) są generowane zadaniem Celery po
opłaceniu zamówienia, numerowane ciągle w obrębie rodzaju i roku, zapisywane
jako PDF w prywatnym buckecie i udostępniane adresem podpisanym na czas.
Aplikacje klienckie wyłącznie pobierają dokument — nigdy go nie składają.
Generowanie po stronie klienta odrzucone: numer musi być nadany atomowo
w jednym miejscu, a dokument musi być identyczny niezależnie od platformy.
PDF powstaje z szablonu HTML przez WeasyPrint wywoływany bezpośrednio
z zadania; osobny pakiet integrujący z widokami jest zbędny.

## Consequences

Obraz workera Celery potrzebuje bibliotek systemowych do renderowania (Pango,
Cairo). Sprzedaż jest wyłącznie konsumencka ([ADR 0016](0016-sprzedaz-wylacznie-konsumencka.md)),
więc dokumenty nie trafiają do KSeF; zwolnienie z kasy fiskalnej dla sprzedaży
wysyłkowej wymaga potwierdzenia u księgowości — zapisane w rejestrze otwartych
decyzji.
