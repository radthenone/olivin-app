# Kwoty przechowywane jako liczby całkowite w najmniejszej jednostce waluty

Wszystkie kwoty pieniężne to liczby całkowite groszy wraz z jawnym kodem waluty — nigdy liczby zmiennoprzecinkowe. Liczby zmiennoprzecinkowe nie reprezentują dokładnie wartości dziesiętnych, co w handlu prowadzi do rozjazdów przy sumowaniu koszyka, naliczaniu podatku i uzgadnianiu rozliczeń z operatorem płatności.

## Considered Options

Rozważono typ dziesiętny — poprawny matematycznie, ale wymaga konwersji przy każdym wywołaniu operatora płatności, który operuje w jednostkach minorowych, i pozostawia możliwość przypadkowego rzutowania na typ zmiennoprzecinkowy.

## Consequences

Decyzja na poziomie schematu bazy danych, bardzo kosztowna do odwrócenia. Musi obowiązywać przed powstaniem pierwszego modelu zamówienia. Zaokrąglenie następuje raz, na poziomie pozycji, nigdy w trakcie sumowania.
