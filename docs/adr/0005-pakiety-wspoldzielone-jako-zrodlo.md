# Pakiety współdzielone konsumowane jako źródło TypeScript

Pakiety w monorepo nie mają kroku budowania — aplikacja webowa transpiluje je sama, a bundler mobilny obserwuje ich katalogi. Przy tej skali brak artefaktu kompilacji oznacza brak nieaktualnego katalogu wynikowego do debugowania i brak wpisu pamięci podręcznej do unieważnienia.

## Consequences

Każda aplikacja kompiluje wspólny kod ponownie. Znane ryzyko: domyślny bundler Next.js ma otwarte zgłoszenie dotyczące transpilacji pakietów lokalnych w monorepo — jeśli problem wystąpi, wyjściem jest starszy bundler albo przejście na pakiety kompilowane.
