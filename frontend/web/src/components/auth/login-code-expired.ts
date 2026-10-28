/**
 * Parametr adresu, którym ekran kodu albo MFA wraca na zamówienie kodu, gdy
 * oczekujące logowanie przepadło (#409, #414). Wartość mówi, który komunikat
 * pokazać. Trzymany tu, żeby formularz i trasa używały tych samych wartości.
 */
export const LOGIN_CODE_EXPIRED_PARAM = "expired";

export type LoginCodeExpiredReason = "mfa" | "code";

const EXPIRED_VALUES: Record<LoginCodeExpiredReason, string> = {
  mfa: "1",
  code: "code",
};

export function loginCodeExpiredValue(reason: LoginCodeExpiredReason): string {
  return EXPIRED_VALUES[reason];
}

export function loginCodeExpiredReason(
  value: string | undefined,
): LoginCodeExpiredReason | null {
  if (value === EXPIRED_VALUES.mfa) return "mfa";
  if (value === EXPIRED_VALUES.code) return "code";
  return null;
}
