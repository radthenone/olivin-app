---
status: accepted
supersedes: 0015
---

# Zwrot oddaje najpierw kupon, resztę pieniędzmi — niezależnie od podstawy

Forma rekompensaty nie zależy od podstawy zwrotu, tylko od tego, czym klient
zapłacił. Zwracana kwota wyczerpuje najpierw kuponową część zamówienia, która
nie została jeszcze oddana we wcześniejszych zwrotach, a resztę oddaje
pieniędzmi przez operatora płatności. Klient, który płacił wyłącznie
pieniędzmi, dostaje wyłącznie pieniądze — sklep nie proponuje mu kuponu.
Kuponowa część zaokrąglana jest w górę do pełnych 10 zł, ale nigdy ponad
kuponową część zamówienia, która została do oddania.

Przykład: zamówienie 300 zł, w tym 200 zł kuponem. Zwrot za 180 zł to kupon
180 zł; zwrot za 250 zł to kupon 200 zł i 50 zł pieniędzmi; zwrot całości to
kupon 200 zł i 100 zł pieniędzmi. Zwrot za 185 zł to kupon 190 zł.

Podstawa zwrotu (`ReturnReason`) rozstrzyga nadal o terminie i o tym, czy
zwrot w ogóle przysługuje, ale już nie o formie rekompensaty.

## Considered Options

- **Forma zależna od podstawy** (ADR 0015): zwrot dobrowolny wyłącznie kuponem.
  Odrzucone przez właściciela — sklep nie chce odmawiać pieniędzy klientowi,
  który płacił pieniędzmi.
- **Podział proporcjonalny** kuponu na pozycje według wartości, utrwalany przy
  zamówieniu. Odrzucony na rzecz „najpierw kupon”: prostszy w rozliczeniu
  i zatrzymuje w sklepie więcej wartości w kuponach.
- **Kupon jako opcja domyślna** dla płacących pieniędzmi, z której klient
  musi się wypisać. Odrzucone: przy odstąpieniu i reklamacji kupon wymaga
  wyraźnej zgody, a domyślny wybór nią nie jest.

## Consequences

Przy każdym zwrocie trzeba znać sumę kuponów już oddanych z danego zamówienia —
rozliczenie zależy od kolejności zwrotów. Kupon wydany ze zwrotu zachowuje
powiązanie z zamówieniem źródłowym (ADR 0014). Regulamin zwrotów wymaga
przeglądu przez prawnika, razem z ręczną obsługą odstąpienia przed doręczeniem.
