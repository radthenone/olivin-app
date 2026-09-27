# Rabat jest promocją, kupon jest zapłatą — dwa pojęcia, nie jedno z flagą

Kod rabatowy, obniżka sezonowa na wybrane produkty i stały rabat premium to
**promocje**: obniżają cenę pozycji przed podatkiem. Kupon — zgodnie z
[ADR 0011](0011-kupony-zamiast-salda.md) — jest formą zapłaty naliczaną po
promocjach i tylko za towar. Rozważono jeden model z polem rodzaju
(`payment | discount`) — odrzucone, bo każde miejsce liczące cenę, podatek
i korektę przy zwrocie ([ADR 0014](0014-zwrot-jako-korekta-kupon-jako-zaplata.md))
musiałoby się rozgałęziać; księgowo to dwa różne zdarzenia (obniżenie podstawy
opodatkowania kontra rozliczenie zapłaty).

## Consequences

Na pozycję działa najwyżej jedna promocja — najkorzystniejsza dla klienta; nie
ma priorytetów ani łączenia. Premium nadawane jest automatycznie po
przekroczeniu progu faktycznie zapłaconych kwot za dostarczone zamówienia
i jest bezterminowe; jego rabat to zwykła promocja z warunkiem członkostwa.
Kupon ma nominał z listy, dwanaście miesięcy ważności i kod nadawany wyłącznie
przez sklep; niewykorzystana część przepada.
