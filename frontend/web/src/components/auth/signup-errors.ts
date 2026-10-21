import {
  AuthResponseError,
  mapSignupErrors,
  mapVerifyEmailErrors,
  type SignupError,
  type VerifyEmailError,
} from "@olivin/features/auth";

export type RegisterField =
  | "email"
  | "username"
  | "password"
  | "passwordConfirm"
  | "consentTerms"
  | "consentPrivacy"
  | "consentMarketing";

export type RegisterValidationError = {
  field: RegisterField;
  key: AuthErrorKey;
};

export type AuthErrorKey =
  | "errors.emailInvalid"
  | "errors.emailTaken"
  | "errors.usernameInvalid"
  | "errors.usernameTaken"
  | "errors.passwordTooShort"
  | "errors.passwordConfirmRequired"
  | "errors.passwordMismatch"
  | "errors.passwordInvalid"
  | "errors.consentRequired"
  | "errors.codeInvalid"
  | "errors.tooManyAttempts"
  | "errors.registrationFailed"
  | "errors.verificationFailed";

const REGISTER_FIELDS: ReadonlySet<string> = new Set<RegisterField>([
  "email",
  "username",
  "password",
  "passwordConfirm",
  "consentTerms",
  "consentPrivacy",
  "consentMarketing",
]);

/**
 * Kody walidacji ze schematu `@olivin/schemas` → klucze katalogu tekstów.
 *
 * Formularz nie zna reguł ani tekstów: dostaje pole i klucz, a `t()` z
 * `@olivin/i18n` tłumaczy go na język interfejsu.
 */
export function registerValidationErrors(
  issues: readonly { path: readonly PropertyKey[]; message: string }[],
): RegisterValidationError[] {
  const errors: RegisterValidationError[] = [];
  const seen = new Set<string>();

  for (const issue of issues) {
    const field = issue.path[0];

    if (
      typeof field !== "string" ||
      !REGISTER_FIELDS.has(field) ||
      seen.has(field)
    ) {
      continue;
    }

    seen.add(field);
    errors.push({
      field: field as RegisterField,
      key: validationKey(issue.message),
    });
  }

  return errors;
}

function validationKey(code: string): AuthErrorKey {
  switch (code) {
    case "email_invalid":
      return "errors.emailInvalid";
    case "username_too_short":
    case "username_too_long":
    case "username_invalid":
      return "errors.usernameInvalid";
    case "password_too_short":
      return "errors.passwordTooShort";
    case "password_confirm_required":
      return "errors.passwordConfirmRequired";
    case "password_mismatch":
      return "errors.passwordMismatch";
    case "consent_required":
      return "errors.consentRequired";
    default:
      return "errors.registrationFailed";
  }
}

/**
 * Błąd backendu rejestracji → klucz katalogu.
 *
 * `null` znaczy „pokaż komunikat backendu”: nieznany błąd domenowy bywa
 * czytelniejszy niż ogólne „spróbuj ponownie”.
 */
export function signupErrorKey(error: SignupError): AuthErrorKey | null {
  switch (error.code) {
    case "emailTaken":
      return "errors.emailTaken";
    case "usernameTaken":
      return "errors.usernameTaken";
    case "consentRequired":
      return "errors.consentRequired";
    case "tooManyAttempts":
      return "errors.tooManyAttempts";
    case "invalid":
      if (error.target === "email") return "errors.emailInvalid";
      if (error.target === "username") return "errors.usernameInvalid";
      if (error.target === "password") return "errors.passwordInvalid";
      return "errors.registrationFailed";
    default:
      return error.message ? null : "errors.registrationFailed";
  }
}

/** Błąd backendu weryfikacji kodu → klucz katalogu (albo `null`). */
export function verifyEmailErrorKey(
  error: VerifyEmailError,
): AuthErrorKey | null {
  if (error.code === "codeInvalid") return "errors.codeInvalid";
  if (error.code === "tooManyAttempts") return "errors.tooManyAttempts";
  return error.message ? null : "errors.verificationFailed";
}

/**
 * Błędy pól z odrzuconej rejestracji.
 *
 * Backend odpowiada listą `errors[]` dopiero po sprawdzeniu danych, więc
 * formularz dostaje je przy właściwych polach zamiast jednego komunikatu.
 */
export function registerErrorsFromFailure(
  error: unknown,
): SignupError[] | null {
  return error instanceof AuthResponseError
    ? mapSignupErrors(error.response.data)
    : null;
}

/** Błędy odrzuconego kodu z e-maila. */
export function verifyEmailErrorsFromFailure(
  error: unknown,
): VerifyEmailError[] | null {
  return error instanceof AuthResponseError
    ? mapVerifyEmailErrors(error.response.data)
    : null;
}
