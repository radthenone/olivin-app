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
