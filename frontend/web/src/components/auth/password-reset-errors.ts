import {
  AuthResponseError,
  mapPasswordResetErrors,
  passwordResetErrorCode,
  type PasswordResetError,
} from "@olivin/features/auth";

export type PasswordResetField = "email" | "key" | "password";

export type PasswordResetErrorKey =
  | "errors.emailInvalid"
  | "errors.codeRequired"
  | "errors.passwordTooShort"
  | "errors.generic";

export type PasswordResetValidationError = {
  field: PasswordResetField;
  key: PasswordResetErrorKey;
};

export type PasswordResetFailureKey =
  "errors.codeInvalid" | "errors.codeExpired" | "errors.tooManyAttempts";

const FIELDS: Record<
  string,
  { field: PasswordResetField; fallback: PasswordResetErrorKey }
> = {
  email: { field: "email", fallback: "errors.emailInvalid" },
  key: { field: "key", fallback: "errors.codeRequired" },
  password: { field: "password", fallback: "errors.passwordTooShort" },
};

const MESSAGE_KEYS: Record<string, PasswordResetErrorKey> = {
  email_invalid: "errors.emailInvalid",
  code_required: "errors.codeRequired",
  password_too_short: "errors.passwordTooShort",
};

/**
 * Kody walidacji ze schematu `@olivin/schemas` → pole i klucz katalogu.
 *
 * Formularz nie zna reguł ani tekstów: dostaje pole i klucz, a `t()` z
 * `@olivin/i18n` tłumaczy go na język interfejsu. Każde pole dostaje jeden
 * komunikat, żeby nie zasypywać klienta powtórzeniami.
 */
export function passwordResetValidationErrors(
  issues: readonly { path: readonly PropertyKey[]; message: string }[],
): PasswordResetValidationError[] {
  const errors: PasswordResetValidationError[] = [];
  const seen = new Set<PasswordResetField>();

  for (const issue of issues) {
    const config = FIELDS[String(issue.path[0])];

    if (!config || seen.has(config.field)) {
      continue;
    }

    seen.add(config.field);
    errors.push({
      field: config.field,
      key: MESSAGE_KEYS[issue.message] ?? config.fallback,
    });
  }

  return errors;
}

/**
 * Błędy pól z odrzuconego resetu allauth.
 *
 * Wspólny `useResetPassword` rzuca `AuthResponseError` dla statusów spoza
 * protokołu sesji (np. 400 ze złym kodem), więc formularz dostaje błędy przy
 * właściwych polach zamiast jednego komunikatu.
 */
export function passwordResetErrorsFromFailure(
  error: unknown,
): PasswordResetError[] | null {
  return error instanceof AuthResponseError
    ? mapPasswordResetErrors(error.response.data)
    : null;
}

/**
 * Odrzucenie resetu hasła bez błędów pól (#421).
 *
 * Allauth zgłasza limit zamówienia jako 429 bez kodu błędu, a po wyczerpaniu
 * prób kodu etap resetu znika i przychodzi 409. Oba przypadki mają własny
 * komunikat — klient odczekuje albo zamawia nowy kod, zamiast poprawiać kod.
 * `null` znaczy, że błąd nie jest znany i formularz pokazuje komunikat ogólny.
 */
export function passwordResetFailureKey(
  error: unknown,
): PasswordResetFailureKey | null {
  switch (passwordResetErrorCode(error)) {
    case "codeExpired":
      return "errors.codeExpired";
    case "tooManyAttempts":
      return "errors.tooManyAttempts";
    case "codeInvalid":
      return "errors.codeInvalid";
    default:
      return null;
  }
}
