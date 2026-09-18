# Oryginał zdjęcia zachowany, kadr po stronie klienta, buckety według polityki dostępu

Klient wysyła oryginał zdjęcia (wstępnie zmniejszony do rozsądnego rozmiaru)
wraz z prostokątem kadru; backend w zadaniu Celery tnie, skaluje do zestawu
rozmiarów i zapisuje w formacie WebP. Oryginał zostaje w prywatnym buckecie,
żeby zmiana kadru nie wymagała ponownego wgrania. Buckety są trzy, podzielone
polityką dostępu, nie rodzajem treści: `products` (odczyt publiczny),
`originals` (prywatny), `documents` (prywatny, udostępniany adresem
podpisanym na czas — dokumenty sprzedaży, certyfikaty kamieni). Jeden bucket
z prefiksami odrzucony: pomyłka w jednej regule dostępu wystawiłaby faktury
klientów do internetu. Zdjęć profilowych nie ma.

## Consequences

Układ plików w bucketach jest kosztowny do zmiany po zapełnieniu — stąd
decyzja zapisana. Baza przechowuje tylko klucz obiektu bez hosta i bucketa;
adres składa serializer.
