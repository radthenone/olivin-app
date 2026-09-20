"""Adaptery do usług zewnętrznych (ADR 0027).

Tłumaczenie treści, kurs kruszcu, kurs walut, przewoźnicy i powiadomienia
push wchodzą do systemu przez własny interfejs, a konkretny dostawca jest
szczegółem konfiguracji. Żaden identyfikator dostawcy nie trafia do modelu
domenowego poza polem „źródło" przy kursach.
"""
