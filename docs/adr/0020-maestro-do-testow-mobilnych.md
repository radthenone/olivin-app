# Maestro jako narzędzie testów końcowych aplikacji mobilnej

Testy końcowe aplikacji mobilnej powstają w Maestro. Testy są deklarowane
w plikach YAML, a narzędzie działa z aplikacją Expo bez wychodzenia z trybu
zarządzanego.

## Considered Options

Rozważono Detox — mocniejszy i bardziej precyzyjny, ale wymaga trybu bare albo
uprzedniego wygenerowania projektu natywnego oraz znacznie większej ilości
konfiguracji. Przy obecnym ustawieniu projektu byłby to koszt ponoszony zanim
istnieje przepływ wart pokrycia.

## Consequences

Pierwsze testy powstają dopiero, gdy istnieje przepływ wart pokrycia, czyli po
zbudowaniu kasy. Wybór narzędzia zapada teraz, żeby nie blokować tamtej pracy,
ale sam nie tworzy zobowiązania do pisania testów wcześniej.

Sprawa pilniejsza niż testy końcowe, odnotowana przy okazji: w CI nie ma dziś
**żadnego** builda ani testu aplikacji mobilnej. Bramki frontendowe to lint,
kontrola typów, kontrola klienta API, Prettier i test przeglądarkowy aplikacji
webowej. Wyszło to przy próbie podniesienia Tailwinda do wersji 4 — zmiana miała
trzy zielone bramki i rozbijała stylowanie pod NativeWindem, bo nic jej nie
sprawdzało. Sam smoke test builda aplikacji mobilnej jest wart wprowadzenia
wcześniej niż pełne testy końcowe.
