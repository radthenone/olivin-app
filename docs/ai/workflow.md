# Workflow pracy z AI w olivin-app

## Cel

Ten dokument opisuje praktyczny sposób pracy z agentami AI w projekcie `olivin-app`.
Łączy lokalne zasady repo z dobrymi praktykami podejścia podobnego do `obra/superpowers`, ale bez ślepego kopiowania zewnętrznego workflow.

## Zasada nadrzędna

AI ma pomagać w analizie, planowaniu i implementacji, ale nie może zastępować realnej analizy repozytorium.
Najpierw repo, potem diagnoza, potem plan, na końcu kod.

## Podstawowy przepływ pracy

### 1. Analiza kontekstu

Przed każdą odpowiedzią techniczną agent powinien:

- sprawdzić realne pliki i katalogi,
- wskazać ścieżki związane z problemem,
- oddzielić fakty od założeń,
- dopiero potem formułować rekomendacje.

### 2. Dobór trybu pracy

Dobierz tryb pracy do zadania.

#### Bugfix

Użyj trybu bugfix, gdy trzeba:

- ustalić objaw,
- znaleźć przyczynę źródłową,
- zaproponować minimalną poprawkę,
- ocenić ryzyko regresji.

#### Feature

Użyj trybu feature, gdy trzeba:

- wskazać miejsce funkcjonalności w architekturze,
- ocenić wpływ na frontend, backend i API,
- zaproponować etapowy plan wdrożenia.

#### Refactor

Użyj trybu refactor, gdy trzeba:

- poprawić strukturę kodu bez zmiany zachowania biznesowego,
- zmniejszyć coupling,
- poprawić testowalność,
- uprościć przepływ danych.

## Jak korzystać z podejścia podobnego do superpowers

Z podejścia podobnego do `obra/superpowers` warto zachować:

- lepszą diagnozę problemu,
- planowanie większych zmian,
- systematyczne debugging i verification-before-completion,
- myślenie w trybie minimalnej, bezpiecznej zmiany.

Nie warto kopiować bezpośrednio:

- obcych założeń o strukturze projektu,
- zbyt ciężkiego procesu dla małych zmian,
- sztywnego workflow tam, gdzie lokalna poprawka jest wystarczająca.

## Reguły językowe

W projekcie obowiązuje:

- język odpowiedzi: polski,
- język docstringów: polski,
- język nazw technicznych: angielski.

## Reguły jakości

Każda odpowiedź techniczna powinna zawierać:

1. krótką diagnozę,
2. wskazanie plików,
3. listę ryzyk,
4. plan zmian,
5. informację, czego nie udało się potwierdzić.

## Kiedy nie komplikować procesu

Nie uruchamiaj rozbudowanego procesu planowania, jeśli:

- problem jest lokalny i dobrze rozpoznany,
- poprawka dotyczy jednego lub kilku blisko powiązanych plików,
- ryzyko regresji jest niskie,
- nie ma zmiany kontraktu API ani zmiany architektury.

## Kiedy rozszerzyć analizę

Rozszerz analizę, jeśli zmiana dotyka:

- przepływu danych frontend-backend,
- auth,
- płatności,
- kontraktu API,
- cache i invalidation,
- side effectów lub operacji asynchronicznych,
- wielu modułów naraz.
