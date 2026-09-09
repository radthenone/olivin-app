# Płatności przez Payment Intents z gotowymi elementami operatora

Płatności realizowane są przez intencje płatnicze po stronie backendu oraz gotowe komponenty operatora po stronie klienta — arkusz wysuwany od dołu na mobile i osadzony element na webie. Jedna integracja backendowa obsługuje oba cele, dane kart nigdy nie trafiają na nasz serwer, a uwierzytelnianie płatności obsługuje operator.

## Considered Options

Rozważono płatność hostowaną w całości u operatora — odrzucona z powodu braku kontroli nad przebiegiem kasy. Rozważono własne pola płatnicze — odrzucone z powodu zakresu zgodności z normami kart płatniczych i konieczności utrzymania dwóch osobnych implementacji.

## Consequences

Metody płatności właściwe dla polskiego rynku są konfigurowane po stronie operatora, bez zmian w kodzie. Kwota do zapłaty jest zawsze wyliczana na backendzie; zdarzenie od operatora jest jedynym źródłem prawdy o dokonaniu płatności i musi być odporne na wielokrotne dostarczenie.
