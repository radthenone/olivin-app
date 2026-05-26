## Zakres

- [ ] Zmiana dotyczy backendu
- [ ] Zmiana dotyczy frontendu
- [ ] Zmiana dotyczy kontraktu API
- [ ] Zmiana dotyczy konfiguracji, CI lub workflow

## Kontrola jakości

- [ ] Uruchomiono adekwatne testy backendu: `task test:backend-local -- <ścieżka>`
- [ ] Uruchomiono Ruff: `task lints:backend:ruff:check` albo `task lints:backend:ruff`
- [ ] Uruchomiono MyPy: `task lints:backend:typecheck`
- [ ] Uruchomiono lint frontendu: `task lints:frontend:lint:check` albo `task lints:frontend:lint`
- [ ] Uruchomiono typecheck frontendu: `task lints:frontend:typecheck`

## Kontrakt API

- [ ] Zmiana nie wpływa na API
- [ ] Zmieniono serializer, viewset, URL albo schema endpointu
- [ ] Po zmianie API uruchomiono `task ovral:generate`
- [ ] Po regeneracji klienta uruchomiono `task lints:frontend:typecheck`

## Uwagi

Opisz krótko ryzyka, decyzje projektowe i rzeczy, których nie udało się potwierdzić.
