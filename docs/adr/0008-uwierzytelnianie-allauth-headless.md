# Uwierzytelnianie przez django-allauth headless, nie JWT

Uwierzytelnianie opiera się na django-allauth w trybie headless, obsługującym logowanie hasłem, kodem jednorazowym, dostawcami zewnętrznymi oraz drugim składnikiem. Rozróżniane są dwa klienty: przeglądarkowy, przenoszący sesję w ciasteczkach, oraz aplikacyjny, przenoszący ją w nagłówku.

## Consequences

Zależność od tokenów JWT obecna w pliku zależności backendu jest pozostałością i powinna zostać usunięta — dwa równoległe mechanizmy uwierzytelniania w jednym projekcie to typowe źródło luk, bo jeden bywa pilnowany, a drugi zapominany.
