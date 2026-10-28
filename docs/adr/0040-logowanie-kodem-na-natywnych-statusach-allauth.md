# Logowanie kodem na natywnych statusach allauth

Limity i błędy logowania jednorazowym kodem zwracamy tak, jak robi to django-allauth, bez nadpisywania widoków. Przekroczenie limitu zamówień kodu (`request_login_code`) daje 400 z kodem `too_many_login_attempts`. Zły kod daje 400 z kodem `incorrect_code`. Gdy kod wygaśnie albo wyczerpią się próby (`ACCOUNT_LOGIN_BY_CODE_MAX_ATTEMPTS`), etap potwierdzenia znika i kolejne potwierdzenie dostaje 409 bez listy błędów. Próba, która dobija limit, dostaje jeszcze zwykłe `incorrect_code`.

Klienci web i mobile rozpoznają te przypadki jednym mapperem `loginCodeErrorCode` w `@olivin/features/auth`: limit po kodzie błędu, a nie po statusie, 409 jako przepadły kod. Po 409 klient wraca do zamówienia nowego kodu, bo wpisywanie kolejnych kodów nic nie da. Status 429 może przyjść tylko z proxy i też oznacza limit.

## Considered Options

- **429 przy każdym limicie.** Odrzucone. Wymaga nadpisania widoków allauth, utrzymania ich przy aktualizacjach i regeneracji schematu OpenAPI oraz klienta Orval. Zysk to tylko inny status przy tym samym komunikacie.
- **Rozróżnienie limitu prób od wygasłego kodu przy 409.** Odrzucone. Allauth nie mówi, dlaczego etap zniknął, a w obu przypadkach użytkownik robi to samo: zamawia nowy kod.

## Consequences

Testy backendu (#407) sprawdzają natywne statusy. Inne ścieżki auth (np. reset hasła) nadal rozpoznają limit po 429 i nie są objęte tą decyzją.
