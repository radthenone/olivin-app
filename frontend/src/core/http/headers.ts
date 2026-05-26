import { allauthClient } from "@core/config/platform";
import { sessionTokenStorage } from "@core/auth/session-token.storage";
import { ensureCsrfCookie, getCsrfTokenFromCookie } from "@core/auth/csrf";
import { ENV } from "@core/config/env";
import type { HttpRequestConfig } from "./types";

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

/**
 * Buduje techniczne nagłówki HTTP dla każdego requestu.
 *
 * Dlaczego istnieje:
 * - browser potrzebuje cookie + CSRF,
 * - app potrzebuje X-Session-Token,
 * - reszta aplikacji nie powinna znać tych szczegółów transportu.
 */
export async function buildHeaders(
  config: HttpRequestConfig,
): Promise<Headers> {
  const method = (config.method ?? "GET").toUpperCase();
  const headers = new Headers({
    Accept: "application/json",
    "Content-Type": "application/json",
    "X-Api-Version": ENV.APP_VERSION,
  });

  new Headers(config.headers).forEach((value, key) => {
    headers.set(key, value);
  });

  if (allauthClient === "browser" && UNSAFE_METHODS.has(method)) {
    await ensureCsrfCookie();

    const csrfToken = getCsrfTokenFromCookie();
    if (csrfToken) {
      headers.set("X-CSRFToken", csrfToken);
    }
  }

  if (allauthClient === "app") {
    const sessionToken = await sessionTokenStorage.get();
    if (sessionToken) {
      headers.set("X-Session-Token", sessionToken);
    }
  }

  return headers;
}
