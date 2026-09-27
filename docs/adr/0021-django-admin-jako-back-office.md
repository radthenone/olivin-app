# Django admin jako back office, bez budowania własnego panelu

Obsługa zamówień, magazynu, zwrotów i moderacji opinii odbywa się w panelu
administracyjnym Django. Własny interfejs nie powstaje.

Dopuszczalna jest nakładka wyglądowa pokroju `django-unfold`, o ile pozostaje
warstwą prezentacji nad standardowym panelem. Nakładka poprawia wygląd i wygodę
bez zmiany modelu pracy, więc jej wprowadzenie lub usunięcie jest odwracalne.

## Considered Options

Rozważono własny panel. Odrzucony na tym etapie: to w praktyce drugi interfejs do
zbudowania i utrzymania, konkurujący o czas z budową sklepu, zanim w ogóle
wiadomo, które przepływy pracy okażą się uciążliwe.

## Consequences

Panel administracyjny Django słabo znosi złożone przepływy pracy, takie jak
kompletacja zamówienia czy obsługa zwrotu. Gdy konkretny przepływ zacznie
przeszkadzać, poza panel wypychany jest **ten jeden ekran**, nie cały back
office. Odwrócenie pozostaje więc tanie i przyrostowe.

Nakładka nie może przejmować logiki domenowej. Reguły takie jak dopuszczalna
forma rekompensaty przy zwrocie, opisana w
[ADR 0015](0015-podstawa-zwrotu-decyduje-o-formie-rekompensaty.md), należą do
modelu i muszą obowiązywać niezależnie od tego, czy zmiana wychodzi z panelu,
czy z interfejsu programistycznego.
