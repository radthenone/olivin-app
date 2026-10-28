# Reset hasła na natywnych statusach allauth

Reset hasła zostaje na odpowiedziach, które django-allauth zwraca sam, bez nadpisywania widoków — tak samo jak logowanie kodem (ADR 0040). Sprawdzone testem backendu (`backend/src/tests/accounts/test_password_reset_by_code.py`):

- limit zamówienia resetu (`reset_password`: `10/m/ip,5/m/key`) daje **429** z ciałem `{"status": 429}` i **bez kodu błędu** — allauth używa tu `RateLimitResponse` z `consume_or_429`, a nie walidacji z kodem jak przy logowaniu kodem,
- zły kod resetu daje **400** z błędem przy polu `key` i kodem `incorrect_code`,
- po wyczerpaniu `PASSWORD_RESET_BY_CODE_MAX_ATTEMPTS` (domyślnie 3) allauth kasuje etap resetu z sesji, więc kolejne ustawienie hasła dostaje **409** z ciałem `{"status": 409}`.

Klienci web i mobile rozpoznają te przypadki jednym mapperem `passwordResetErrorCode` w `@olivin/features/auth`: 429 to limit (natywny allauth albo proxy), 409 to przepadły etap resetu, a `incorrect_code` to zły kod. Kod `too_many_password_reset_attempts` jest rozpoznawany, gdyby backend albo proxy dołożyły go do odpowiedzi, ale allauth go nie wysyła. Formularz prośby pokazuje „odczekaj”, a ekran ustawienia hasła po 409 wraca do zamówienia nowego kodu — wpisywanie kolejnych kodów nic nie da.

## Considered Options

- **429 zamienić na 400 z kodem limitu (jak logowanie kodem).** Odrzucone. Wymaga nadpisania widoku allauth i utrzymania go przy aktualizacjach oraz regeneracji schematu OpenAPI i klienta Orval. Zysk to tylko inny status przy tym samym komunikacie.
- **Odgadywać po 409, czy kod wygasł, czy skończyły się próby.** Odrzucone. Allauth nie mówi, dlaczego etap zniknął, a w obu przypadkach użytkownik robi to samo: zamawia nowy kod.

## Consequences

E2E resetu hasła używa natywnych odpowiedzi: 429 dla limitu zamówienia i 409 po wyczerpaniu prób. Inne ścieżki auth pozostają przy swoich mapperach; ADR 0040 opisuje logowanie kodem.
