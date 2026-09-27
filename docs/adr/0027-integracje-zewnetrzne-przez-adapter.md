# Integracje zewnętrzne przez adapter, pierwszy dostawca wybierany później

Tłumaczenie treści, kurs kruszcu, kurs walut, przewoźnicy i powiadomienia push
wchodzą do systemu przez własny interfejs adaptera, a konkretny dostawca jest
szczegółem konfiguracji. Ustalone kierunki: tłumaczenia — DeepL w produkcji,
LibreTranslate w środowisku deweloperskim; kurs walut — Narodowy Bank Polski;
przewoźnicy — InPost ShipX jako pierwszy, Furgonetka jako drugi dla pozostałych
i zagranicy (zamiast osobnej integracji z każdym przewoźnikiem); push — usługa
Expo. Dostawca kursu kruszcu nierozstrzygnięty; do czasu wyboru kurs wpisuje
się ręcznie. Na start etykiety i numery śledzenia są wpisywane ręcznie
w panelu — adapter przewoźnika to późniejszy bilet.

## Consequences

Żaden identyfikator dostawcy nie trafia do modelu domenowego poza polem
„źródło” przy kursach. Zamiana dostawcy to nowy adapter i zmiana konfiguracji,
nie migracja danych.
