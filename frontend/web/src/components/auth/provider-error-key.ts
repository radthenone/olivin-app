export type ProviderErrorKey =
  | "auth.provider.errors.cancelled"
  | "auth.provider.errors.notAllowed"
  | "auth.provider.errors.reauthentication"
  | "auth.provider.errors.failed";

/**
 * Kod błędu z `callback_url` allauth → klucz katalogu tekstów.
 *
 * Anulowanie u dostawcy (`access_denied`, `cancelled`) nie jest awarią, więc
 * dostaje osobny komunikat. Odmowa polityki rejestracji i wymóg ponownego
 * logowania też mają własne teksty, a reszta ląduje w komunikacie ogólnym.
 */
export function providerErrorKey(code: string | null | undefined): ProviderErrorKey {
  switch (code) {
    case "access_denied":
    case "cancelled":
      return "auth.provider.errors.cancelled";
    case "denied":
    case "permission_denied":
    case "signup_closed":
      return "auth.provider.errors.notAllowed";
    case "reauthentication_required":
      return "auth.provider.errors.reauthentication";
    default:
      return "auth.provider.errors.failed";
  }
}
