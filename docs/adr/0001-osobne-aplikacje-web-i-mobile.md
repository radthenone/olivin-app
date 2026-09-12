# Web i mobile jako osobne aplikacje w jednym monorepo

Sklep potrzebuje witryny indeksowanej przez wyszukiwarki oraz aplikacji mobilnej, a te dwie rzeczy pełnią w handlu różne role: web pozyskuje klienta i obsługuje pierwszy zakup, aplikacja służy powrotom. Zamiast jednej bazy kodu Expo obsługującej oba cele budujemy dwie aplikacje w monorepo, dzieląc logikę, typy i tokeny designu, ale nie komponenty interfejsu.

## Considered Options

Rozważono jedną aplikację Expo renderowaną statycznie na web — odrzucona z trzech powodów: React Native Web nie produkuje semantycznego HTML, nie ma optymalizacji obrazów, a renderowanie odbywa się wyłącznie w czasie budowania, co źle pasuje do cen powiązanych z kursem kruszcu i zmiennych stanów magazynowych.

## Consequences

Uwierzytelnianie, katalog i kasa powstają po stronie webowej od nowa; aplikacja Expo zachowuje swoją wartość jako klient mobilny. Nowsze wydania Expo osłabiły część argumentów przeciw jego wersji webowej — dwa pozostałe (semantyczny HTML, optymalizacja obrazów) nie zmalały.
