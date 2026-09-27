# Usunięcie konta to anonimizacja, nie kasowanie

Klient usuwa konto samodzielnie z profilu po potwierdzeniu hasłem albo kodem.
Dane osobowe na koncie, profilu i adresach zostają wymazane, logowanie
zablokowane, listy i urządzenia skasowane — ale zamówienia i dokumenty
sprzedaży pozostają w formie bezosobowej przez okres wymagany prawem
podatkowym. Twarde kasowanie odrzucone: naruszałoby obowiązek przechowywania
dokumentów. Usunięcie jest zablokowane, dopóki trwa niedostarczone
zamówienie. Eksport danych odbywa się na wniosek, poleceniem zarządzającym —
bez punktu końcowego w API, bo wnioski są rzadkie.

## Consequences

Zgody klienta są wersjonowane osobnym pojęciem (`Consent`), a zgody na pliki
cookie żyją wyłącznie w przeglądarce. Analityka web to Umami bez ciasteczek
i bez identyfikacji osoby, więc nie wymaga zgody; Google Analytics odrzucone
z powodu wymogu zgody i ładowania po kliknięciu.
