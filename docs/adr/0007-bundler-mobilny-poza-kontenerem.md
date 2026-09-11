# Bundler aplikacji mobilnej działa poza kontenerem

Backend i aplikacja webowa działają jako usługi kontenerowe, ale bundler Metro uruchamiany jest natywnie. Powód jest praktyczny: obserwowanie zmian plików przez montowany wolumin z systemu Windows do kontenera Linuksa jest zawodne i wymaga odpytywania, emulator Androida działa na hoście, a klient deweloperski wykrywa bundler przez sieć lokalną, której kontener domyślnie nie widzi.

## Consequences

Środowisko deweloperskie jest niejednorodne — część usług w kontenerach, jedna poza. Obie aplikacje startują niezależnie, każda jedną komendą.
