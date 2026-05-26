import { allauthClient, isNative } from "@core/config/platform";
import { ENDPOINTS } from "@core/config/endpoints";

/**
 * Pobiera wartość pliku cookie według jego nazwy.
 * @param name -Nazwa pliku cookie do pobrania.
 * @returns Wartość pliku cookie lub wartość null, jeśli nie została znaleziona.
 */
export function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;

  const cookie = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${name}=`));

  return cookie ? decodeURIComponent(cookie.split("=")[1] ?? "") : null;
}

/**
 * Pobiera token CSRF z pliku cookie. Jeśli aplikacja jest uruchomiona w środowisku natywnym i klientem allauth jest "app", zwraca null, ponieważ token CSRF nie jest używany w tym przypadku.
 * @returns Token CSRF lub wartość null, jeśli token nie jest dostępny.
 */
export function getCsrfTokenFromCookie(): string | null {
  if (isNative && allauthClient === "app") return null;

  return getCookie("csrftoken");
}

/**
 * Dba o to, aby browser miał ustawione ciasteczko CSRF przed requestem mutującym.
 */
export async function ensureCsrfCookie() {
  if ((isNative && allauthClient === "app") || getCsrfTokenFromCookie()) return;

  await fetch(`${ENDPOINTS.ALLAUTH.SESSION}`, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });
}
