# Task jako jedyny interfejs komend, Turborepo jako silnik pod spodem

Repozytorium ma rozbudowany zestaw komend Task obejmujący kontenery, migracje bazy i emulator Androida, a Turborepo dostarcza graf zależności i pamięć podręczną zadań JavaScriptu — żadne z tych narzędzi nie zastępuje drugiego. Człowiek uruchamia wyłącznie komendy Task; te tam, gdzie ma to sens, wywołują Turborepo.

## Consequences

Jeden zestaw komend do zapamiętania. Cena: pośrednictwo, przez które komunikat błędu z Turborepo dociera do użytkownika o jedną warstwę dalej.
