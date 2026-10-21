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
