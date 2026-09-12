# Tokeny designu jako obiekt TypeScript, nie preset Tailwinda

Aplikacja mobilna używa NativeWind, którego wersja produkcyjna celuje w Tailwind CSS v3, a aplikacja webowa używa shadcn/ui celującego w v4 — wspólny preset Tailwinda między tymi wersjami nie istnieje. Źródłem prawdy dla palety, typografii i skali odstępów jest więc zwykły obiekt TypeScript, a każda aplikacja zawiera cienki adapter przekładający go na własną formę konfiguracji.

## Consequences

Gdy NativeWind przejdzie na Tailwind v4, wyrzucany jest jeden adapter, a tokeny pozostają nietknięte. Cena: dwa adaptery do utrzymania zamiast jednego pliku konfiguracji.
