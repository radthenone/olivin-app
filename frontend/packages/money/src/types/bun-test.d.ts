// Typy `bun:test` dostarcza pakiet `bun-types`, którego nie ma w tym
// workspace (instalacja paczek należy do CI). Skrócona deklaracja modułu
// wystarcza, żeby typecheck pakietu nie wywalał się na plikach testów —
// uruchomienie i tak robi Bun, a asercje sprawdza jego runner.
declare module "bun:test";
