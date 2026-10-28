import type { LoginCodeErrorCode } from "@olivin/features/auth";
import type { ZodError } from "zod";

/**
 * Komunikaty walidacji logowania kodem.
 *
 * Schematy mieszkają od #405 w `@olivin/schemas`, a wspólny pakiet nie zna
 * języka interfejsu — zwraca kody (`email_invalid`, `code_required`) zamiast
 * tekstów. Tłumaczenie kodu na zdanie jest zadaniem aplikacji.
 */
const LOGIN_CODE_MESSAGES: Record<string, string> = {
  email_invalid: "Podaj poprawny adres email.",
  code_required: "Podaj kod logowania z wiadomości email.",
};

/** Zamienia kod walidacji ze wspólnego schematu na komunikat ekranu. */
export function loginCodeValidationMessage(
  error: ZodError,
  fallback: string,
): string {
  const [issue] = error.issues;

  return (issue && LOGIN_CODE_MESSAGES[issue.message]) || fallback;
}

const LOGIN_CODE_FAILURE_MESSAGES: Record<
  Exclude<LoginCodeErrorCode, "backend">,
  string
> = {
  tooManyAttempts: "Zbyt wiele prób. Odczekaj chwilę.",
  codeExpired: "Kod wygasł albo wykorzystano limit prób. Wyślij nowy kod.",
  codeInvalid: "Kod jest nieprawidłowy lub wygasł.",
};

/** Zamienia kod odrzucenia z `loginCodeErrorCode` na komunikat ekranu (#414). */
export function loginCodeFailureMessage(
  code: LoginCodeErrorCode,
  fallback: string,
): string {
  return code === "backend" ? fallback : LOGIN_CODE_FAILURE_MESSAGES[code];
}
