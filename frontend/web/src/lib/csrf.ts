const CSRF_COOKIE_NAME = "csrftoken";

/**
 * Czyta pojedyncze ciasteczko bez zależności od `document`.
 *
 * Dzięki temu ten sam kod działa w przeglądarce i w teście jednostkowym.
 */
export function getCookieValue(cookie: string, name: string): string | null {
  const entry = cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${name}=`));

  return entry ? decodeURIComponent(entry.slice(name.length + 1)) : null;
}

/**
 * Zapewnia token CSRF dla mutacji w trybie przeglądarkowym allauth.
 *
 * django-allauth zakłada ciasteczko `csrftoken` w odpowiedzi na GET sesji.
 * Gdy ciasteczka jeszcze nie ma, robimy dokładnie ten jeden request — bez
 * niego przeglądarka nie ma czego wstawić do nagłówka `X-CSRFToken`.
 */
export async function ensureCsrfToken(
  sessionUrl: string,
): Promise<string | null> {
  if (typeof document === "undefined") return null;

  const existing = getCookieValue(document.cookie, CSRF_COOKIE_NAME);
  if (existing) return existing;

  try {
    await fetch(sessionUrl, {
      method: "GET",
      credentials: "include",
      headers: { accept: "application/json" },
    });
  } catch {
    // Brak sieci i tak wyjdzie na właściwym żądaniu; tutaj nie maskujemy go
    // drugim błędem.
    return null;
  }

  return getCookieValue(document.cookie, CSRF_COOKIE_NAME);
}
