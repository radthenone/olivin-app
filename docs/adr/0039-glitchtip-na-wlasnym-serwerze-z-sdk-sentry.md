# GlitchTip na własnym serwerze, z SDK Sentry

Błędy z webu, aplikacji mobilnej i Django (razem z Celery) zbiera samodzielnie hostowany GlitchTip. Działa jako usługa w `docker-compose.prod.yml` na tym samym serwerze, korzysta z istniejącego Postgresa i potrzebuje około 256–512 MB RAM. Aplikacje używają oficjalnych SDK Sentry, a DSN wskazuje na GlitchTip. Wszystkie dane zdarzeń zostają na naszym serwerze, więc polityka prywatności nie zyskuje podprocesora z USA.

Zakres:
- błędy na wszystkich platformach,
- śledzenie wydajności z próbkowaniem 10%,
- bez nagrywania sesji.

`sendDefaultPii` jest wyłączone. `beforeSend` usuwa e-maile, adresy, telefony, tokeny i treść formularzy kasy, a użytkownik jest identyfikowany wyłącznie przez ID.

Cztery krytyczne zadania okresowe (pobranie kursu kruszcu, kurs euro, przeliczenie cen, wygaszanie rezerwacji) po udanym wykonaniu wołają adres monitora heartbeat w GlitchTip. Gdy wywołania ustaną, przychodzi alert, bo zatrzymane Celery Beat samo nie zgłasza żadnego błędu. Alerty idą e-mailem, bez dodatkowych integracji.

Logi kontenerów rotuje sterownik `local` Dockera, a gunicorn pisze dziennik dostępu na standardowe wyjście. Nie ma osobnego stosu logów.

## Considered Options

- **Sentry SaaS w regionie EU.** Brak utrzymania i potwierdzone wysyłanie source map, ale konta i DSN leżą w USA, więc trzeba wpisać podprocesora. To plan awaryjny, jeśli source mapy w GlitchTip nie zadziałają.
- **Samodzielnie hostowany Sentry.** Odrzucony, bo wymaga co najmniej 4 rdzeni i 16 GB RAM.
- **Loki i Grafana na logi.** Odrzucone jako nieproporcjonalne do skali.

## Consequences

GlitchTip trzeba aktualizować i obejmować kopiami zapasowymi. Główne ryzyko to source mapy: nie udało się potwierdzić, że pluginy Sentry dla Next i Expo poprawnie wysyłają je do GlitchTip. Plasterek obserwowalności zaczyna się więc od małego testu: jeden celowy błąd na webie i jeden na Androidzie, a potem sprawdzenie, czy stos wywołań jest czytelny. Jeśli nie, wracamy do Sentry w regionie EU, a wymiana DSN nie wymaga zmian w kodzie. Aktualizacje OTA (EAS Update) wymagałyby ręcznego wysyłania source map i są poza zakresem tej decyzji.
