/**
 * authService.ts (features/auth)
 *
 * Fasada z warstwy feature/auth re-eksportująca core/auth/auth.service.
 * Użyj tego pliku importując serwisy w komponentach feature/auth.
 *
 * Dlaczego fasada a nie bezpośredni import?
 * → Pozwala na łatwe podmienienie implementacji (np. mock w testach)
 * → Izoluje feature od szczegółów implementacji core
 */
export * from "@core/auth/auth.service";
