# Hooki Orvala wprost, logika domeny w pakiecie features

Obie aplikacje biorą odczyty, mutacje i klucze zapytań bezpośrednio z hooków generowanych przez Orval w `@olivin/api`. Invalidacja zawsze używa wygenerowanych funkcji `getXxxQueryKey`, a ręczne fabryki kluczy znikają. Hooki z logiką wykraczającą poza pojedyncze wywołanie API trafiają do nowego pakietu `@olivin/features`, podzielonego na podścieżki per obszar domeny (`@olivin/features/cart`, `/catalog`, `/account`…). Chodzi o hooki, które składają kilka zapytań, invalidują kilka kluczy, scalają stan gościa po zalogowaniu albo wyrażają regułę domeny. Prosty `useQuery` na jeden endpoint interfejs woła wprost z Orvala, bez opakowania.

Stan zależny od platformy, na przykład token koszyka gościa albo lokalne ulubione, zapisuje się przez adapter magazynu wstrzykiwany przy starcie aplikacji. To ten sam wzorzec co transport z [ADR 0006](0006-transport-wstrzykiwany-do-klienta-api.md). Schematy formularzy mieszkają w `@olivin/schemas` i powstają na bazie schematów zod z Orvala.

## Considered Options

- **Ręczne serwisy i klucze w każdej aplikacji.** To stan z mobile w chwili tej decyzji. Odrzucone, bo tworzy drugi zestaw kluczy, którego invalidacja nie trafia w hooki Orvala, a na webie trzeba by to samo napisać drugi raz, wbrew [ADR 0001](0001-osobne-aplikacje-web-i-mobile.md) i [ADR 0005](0005-pakiety-wspoldzielone-jako-zrodlo.md).
- **Hooki domenowe w `@olivin/api`.** Odrzucone, bo pakiet klienta i transportu zacząłby wiedzieć o domenie sklepu.

## Consequences

Istniejące hooki mobile przechodzą do pakietu dopiero wtedy, gdy plasterek i tak ich dotyka. Auth przechodzi w fundamencie, bo potrzebuje go logowanie na webie. Account i profile przechodzą w plasterku konta. Do tego czasu w mobile współistnieją oba style.
