# Push przez usługę Expo, z minimum treści

Powiadomienia push na mobile wysyłamy przez usługę push Expo (`expo-notifications`, tokeny Expo, istniejący adapter w backendzie), a nie bezpośrednio przez FCM i APNs. Klucze FCM i APNs przechowuje Expo, więc nie obsługujemy dwóch protokołów. Adapter ([ADR 0027](0027-integracje-zewnetrzne-przez-adapter.md)) pozwala zmienić dostawcę bez migracji danych.

Treść pusha ogranicza się do ogólnego tytułu i adresu do nawigacji (`data.url`). Nie zawiera kwot, adresów ani numerów przesyłek. Pełna treść czeka w skrzynce powiadomień w aplikacji. Mniej danych trafia wtedy do podprocesora w USA, a ekran blokady nie zdradza szczegółów zakupu biżuterii.

Na Androidzie są dwa kanały: `orders` dla komunikatów transakcyjnych, z wysokim priorytetem, oraz `marketing` dla promocji i obserwowanych wariantów, z priorytetem domyślnym. O zgodę systemową pytamy dopiero w chwili korzyści, czyli po złożeniu zamówienia albo przy włączeniu obserwowania. Odmowy nie ponawiamy, a w ustawieniach jest link do ustawień systemu. Wylogowanie najpierw próbuje wyrejestrować urządzenie, ale nie zależy od sieci. Martwe tokeny sprząta backend. Web push pomijamy.

## Considered Options

- **Bezpośrednio FCM i APNs.** Odrzucone. Klucze i tak trzeba założyć, a do tego dochodzą dwa protokoły do utrzymania, bez korzyści przy tej skali.
- **Pełna treść w pushu.** Odrzucone ze względu na podprocesora w USA i ekran blokady.
- **Web push.** Odrzucone. Na iOS działa tylko po dodaniu strony do ekranu głównego, a web ma e-mail i skrzynkę powiadomień.

## Consequences

Backend dostaje w jednym tickecie:
- sprawdzanie potwierdzeń dostarczenia około 15 minut po wysyłce,
- ponawianie z rosnącym odstępem przy błędach 429 i 5xx,
- kanał, priorytet i dźwięk w wiadomości,
- `data.url`.

Zgoda `marketing_push` zostaje zwykłą flagą do czasu opinii prawnika. Push na iOS (klucz APNs) czeka na wydanie iOS.
