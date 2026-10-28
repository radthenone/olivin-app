import type { PasswordResetFailureCode } from "@olivin/features/auth";

/**
 * Komunikaty odrzucenia resetu hasła (#421).
 *
 * Wspólny mapper `passwordResetErrorCode` mówi, co się stało: limit zamówienia
 * (429), przepadły etap resetu (409) albo zły kod. Tłumaczenie kodu na zdanie
 * jest zadaniem aplikacji, tak jak przy logowaniu kodem.
 */
const PASSWORD_RESET_FAILURE_MESSAGES: Record<
  Exclude<PasswordResetFailureCode, "backend">,
  string
> = {
  tooManyAttempts: "Zbyt wiele prób. Odczekaj chwilę.",
  codeExpired: "Kod wygasł albo wykorzystano limit prób. Wyślij nowy kod.",
  codeInvalid: "Kod jest nieprawidłowy lub wygasł.",
};

/** Zamienia kod odrzucenia z `passwordResetErrorCode` na komunikat ekranu. */
export function passwordResetFailureMessage(
  code: PasswordResetFailureCode,
  fallback: string,
): string {
  return code === "backend" ? fallback : PASSWORD_RESET_FAILURE_MESSAGES[code];
}
