import { AuthResponseError } from "./auth-response";

type AllauthError = {
  code?: unknown;
  param?: unknown;
  message?: unknown;
};

export type LoginErrorTarget = "email" | "password" | "form";

export type LoginErrorCode =
  "invalidCredentials" | "tooManyAttempts" | "backend";

export type LoginError = {
  target: LoginErrorTarget;
  code: LoginErrorCode;
  message?: string;
};

const INVALID_CREDENTIAL_CODES = new Set([
  "invalid_login",
  "invalid_credentials",
  "email_password_mismatch",
  "username_password_mismatch",
]);

/**
 * Zamienia błędy allauth na semantyczne błędy formularza logowania.
 *
 * Kody znane interfejsowi dostają własną nazwę i tłumaczenie. Nieznane błędy
 * zachowują pole i komunikat z backendu, żeby nie zgubić informacji, a brak
 * listy błędów kończy się jednym czytelnym błędem formularza.
 */
export function mapLoginErrors(body: unknown): LoginError[] {
  const rawErrors = (body as { errors?: unknown } | null)?.errors;

  if (!Array.isArray(rawErrors) || rawErrors.length === 0) {
    return [{ target: "form", code: "backend" }];
  }

  return rawErrors.map((raw) => {
    const error = raw as AllauthError;
    const target = toTarget(error.param);
    const backendCode = typeof error.code === "string" ? error.code : "";
    const code: LoginErrorCode = INVALID_CREDENTIAL_CODES.has(backendCode)
      ? "invalidCredentials"
      : backendCode === "too_many_login_attempts"
        ? "tooManyAttempts"
        : "backend";

    const message =
      typeof error.message === "string" && error.message.length > 0
        ? error.message
        : undefined;

    return message ? { target, code, message } : { target, code };
  });
}

function toTarget(param: unknown): LoginErrorTarget {
  return param === "email" || param === "password" ? param : "form";
}

export type SignupErrorTarget =
  | "email"
  | "username"
  | "password"
  | "consentTerms"
  | "consentPrivacy"
  | "form";

export type SignupErrorCode =
  | "emailTaken"
  | "usernameTaken"
  | "consentRequired"
  | "invalid"
  | "tooManyAttempts"
  | "backend";

export type SignupError = {
  target: SignupErrorTarget;
  code: SignupErrorCode;
  message?: string;
};

const SIGNUP_PARAMS: Record<string, SignupErrorTarget> = {
  email: "email",
  username: "username",
  password: "password",
  password1: "password",
  password2: "password",
  consent_terms: "consentTerms",
  consent_privacy: "consentPrivacy",
};

/**
 * Zamienia błędy rejestracji allauth na błędy pól formularza.
 *
 * Backend waliduje nazwę użytkownika, hasło i zgodę na dokumenty, więc błąd
 * trafia do właściwego pola. Kody spoza kontraktu zachowują komunikat
 * backendu i lądują na formularzu, żeby użytkownik nie zobaczył pustego błędu.
 */
export function mapSignupErrors(body: unknown): SignupError[] {
  const rawErrors = (body as { errors?: unknown } | null)?.errors;

  if (!Array.isArray(rawErrors) || rawErrors.length === 0) {
    return [{ target: "form", code: "backend" }];
  }

  return rawErrors.map((raw) => {
    const error = raw as AllauthError;
    const target = SIGNUP_PARAMS[String(error.param)] ?? "form";
    const backendCode = typeof error.code === "string" ? error.code : "";
    const message =
      typeof error.message === "string" && error.message.length > 0
        ? error.message
        : undefined;

    const code = toSignupCode(target, backendCode);
    return message ? { target, code, message } : { target, code };
  });
}

function toSignupCode(
  target: SignupErrorTarget,
  backendCode: string,
): SignupErrorCode {
  if (target === "form") {
    return backendCode === "too_many_signup_attempts"
      ? "tooManyAttempts"
      : "backend";
  }

  if (backendCode === "email_taken") {
    return "emailTaken";
  }

  if (backendCode === "username_taken") {
    return "usernameTaken";
  }

  if (
    backendCode === "required" &&
    (target === "consentTerms" || target === "consentPrivacy")
  ) {
    return "consentRequired";
  }

  return "invalid";
}

export type VerifyEmailErrorTarget = "form";

export type VerifyEmailErrorCode =
  "codeInvalid" | "tooManyAttempts" | "backend";

export type VerifyEmailError = {
  target: VerifyEmailErrorTarget;
  code: VerifyEmailErrorCode;
  message?: string;
};

/**
 * Zamienia błędy weryfikacji kodu na błędy formularza.
 *
 * Backend nie mówi, który znak kodu jest zły, więc każdy odrzucony kod daje
 * jeden komunikat o nieprawidłowym lub wygasłym kodzie.
 */
export function mapVerifyEmailErrors(body: unknown): VerifyEmailError[] {
  const rawErrors = (body as { errors?: unknown } | null)?.errors;

  if (!Array.isArray(rawErrors) || rawErrors.length === 0) {
    return [{ target: "form", code: "backend" }];
  }

  return rawErrors.map((raw) => {
    const error = raw as AllauthError;
    const backendCode = typeof error.code === "string" ? error.code : "";
    const message =
      typeof error.message === "string" && error.message.length > 0
        ? error.message
        : undefined;

    const code: VerifyEmailErrorCode =
      backendCode === "too_many_confirm_email_attempts"
        ? "tooManyAttempts"
        : backendCode === "invalid"
          ? "codeInvalid"
          : "backend";

    return message
      ? { target: "form", code, message }
      : { target: "form", code };
  });
}

export type PasswordResetErrorTarget = "email" | "key" | "password" | "form";

export type PasswordResetErrorCode =
  "codeInvalid" | "passwordInvalid" | "tooManyAttempts" | "backend";

export type PasswordResetError = {
  target: PasswordResetErrorTarget;
  code: PasswordResetErrorCode;
  message?: string;
};

const PASSWORD_RESET_PARAMS: Record<string, PasswordResetErrorTarget> = {
  email: "email",
  key: "key",
  password: "password",
};

/**
 * Zamienia błędy resetu hasła na błędy pól formularza.
 *
 * Allauth zwraca odrzucony kod pod `key`, a wymagania hasła pod `password` —
 * dzięki temu kod trafia do pola kodu, a hasło do pola hasła, zamiast jednego
 * komunikatu pod całym formularzem.
 */
export function mapPasswordResetErrors(body: unknown): PasswordResetError[] {
  const rawErrors = (body as { errors?: unknown } | null)?.errors;

  if (!Array.isArray(rawErrors) || rawErrors.length === 0) {
    return [{ target: "form", code: "backend" }];
  }

  return rawErrors.map((raw) => {
    const error = raw as AllauthError;
    const target = PASSWORD_RESET_PARAMS[String(error.param)] ?? "form";
    const backendCode = typeof error.code === "string" ? error.code : "";
    const message =
      typeof error.message === "string" && error.message.length > 0
        ? error.message
        : undefined;

    const code: PasswordResetErrorCode =
      target === "key"
        ? "codeInvalid"
        : target === "password"
          ? "passwordInvalid"
          : backendCode.startsWith("too_many")
            ? "tooManyAttempts"
            : "backend";

    return message ? { target, code, message } : { target, code };
  });
}

export type MfaErrorTarget = "code" | "form";

export type MfaErrorCode = "codeInvalid" | "tooManyAttempts" | "backend";

export type MfaError = {
  target: MfaErrorTarget;
  code: MfaErrorCode;
  message?: string;
};

/**
 * Zamienia błędy potwierdzenia MFA na błędy formularza.
 *
 * Allauth odrzuca zły kod jako `incorrect_code` przy polu `code`, a limit prób
 * zgłasza bez pola — wtedy komunikat trafia na formularz.
 */
export function mapMfaErrors(body: unknown): MfaError[] {
  const rawErrors = (body as { errors?: unknown } | null)?.errors;

  if (!Array.isArray(rawErrors) || rawErrors.length === 0) {
    return [{ target: "form", code: "backend" }];
  }

  return rawErrors.map((raw) => {
    const error = raw as AllauthError;
    const backendCode = typeof error.code === "string" ? error.code : "";
    const target: MfaErrorTarget = error.param === "code" ? "code" : "form";
    const message =
      typeof error.message === "string" && error.message.length > 0
        ? error.message
        : undefined;

    const code: MfaErrorCode =
      backendCode === "incorrect_code"
        ? "codeInvalid"
        : backendCode === "too_many_attempts"
          ? "tooManyAttempts"
          : "backend";

    return message ? { target, code, message } : { target, code };
  });
}

export type LoginCodeErrorCode =
  "codeInvalid" | "codeExpired" | "tooManyAttempts" | "backend";

/**
 * Zamienia odrzucenie zamówienia lub potwierdzenia kodu logowania na kod błędu.
 *
 * Allauth zgłasza limit zamówień jako 400 z kodem `too_many_login_attempts`,
 * a po wyczerpaniu prób albo wygaśnięciu kodu etap potwierdzenia znika i
 * kolejne próby dostają 409 (ADR 0040). 429 przychodzi tylko z proxy.
 */
export function loginCodeErrorCode(error: unknown): LoginCodeErrorCode {
  if (!(error instanceof AuthResponseError)) {
    return "backend";
  }

  const { status, data } = error.response;
  if (status === 429) return "tooManyAttempts";
  if (status === 409) return "codeExpired";

  const rawErrors = (data as { errors?: unknown } | null)?.errors;
  const codes = Array.isArray(rawErrors)
    ? rawErrors.map((raw) => (raw as AllauthError).code)
    : [];

  if (codes.includes("too_many_login_attempts")) return "tooManyAttempts";
  if (codes.includes("incorrect_code")) return "codeInvalid";
  return "backend";
}
