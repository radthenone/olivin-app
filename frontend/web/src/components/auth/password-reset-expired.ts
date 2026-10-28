/**
 * Parametr adresu, którym ekran ustawienia hasła wraca na zamówienie nowego
 * kodu, gdy etap resetu przepadł (#421).
 *
 * Allauth po wyczerpaniu prób kodu kasuje etap z sesji i odpowiada 409, więc
 * wpisywanie kolejnego kodu nic nie da. Wartość mówi formularzowi, który
 * komunikat pokazać; trzymana tutaj, żeby trasa i ekran używały tej samej
 * wartości.
 */
export const PASSWORD_RESET_EXPIRED_PARAM = "expired";

const PASSWORD_RESET_EXPIRED_VALUE = "code";

export function passwordResetExpiredQuery(): string {
  return `${PASSWORD_RESET_EXPIRED_PARAM}=${PASSWORD_RESET_EXPIRED_VALUE}`;
}

export function isPasswordResetExpired(value: string | undefined): boolean {
  return value === PASSWORD_RESET_EXPIRED_VALUE;
}
