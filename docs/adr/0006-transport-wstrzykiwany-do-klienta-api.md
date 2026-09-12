# Transport wstrzykiwany do pakietu klienta API

Klient API jest wspólny dla obu aplikacji, ale sposób przenoszenia sesji nie: mobile wysyła nagłówek z tokenem odczytanym z bezpiecznego magazynu urządzenia, web wysyła ciasteczka wraz z tokenem zabezpieczającym przed fałszowaniem żądań. Pakiet eksponuje jeden punkt konfiguracji przyjmujący implementację transportu, a każda aplikacja dostarcza własną.

## Considered Options

Rozważono rozgałęzienie wewnątrz pakietu przez warunkowe pola eksportu — odrzucone, bo umieszcza wiedzę o platformach w kodzie współdzielonym i każe edytować pakiet przy dodaniu kolejnego celu.
