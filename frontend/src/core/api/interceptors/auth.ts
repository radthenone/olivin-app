/**
 * Interceptor odpowiedzialny za:
 * - Native (app): dodanie X-Session-Token do requestów i odświeżenie tokena z odpowiedzi
 * - Browser (web): withCredentials = true (cookie sesji)
 * - Obsługa 401 / 410 na poziomie interceptora (logowanie błędów, czyszczenie tokena)
 *
 * UWAGA: interceptor NIE nawiguje — to zadanie hooka useAuth w warstwie UI.
 */
import { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { authStorage } from "@core/auth/auth.storage";
import { isNative } from "@lib";
import { CONFIG } from "@core/env";

let csrfInitPromise: Promise<void> | null = null;

function getCookieValue(name: string): string | null {
  if (typeof document === "undefined") return null;
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const cookie of cookies) {
    const [rawKey, ...rest] = cookie.trim().split("=");
    if (rawKey === name) {
      return decodeURIComponent(rest.join("="));
    }
  }
  return null;
}

function isUnsafeMethod(method?: string): boolean {
  const m = (method ?? "get").toLowerCase();
  return m === "post" || m === "put" || m === "patch" || m === "delete";
}

async function ensureWebCsrfCookie(): Promise<void> {
  if (isNative) return;

  // Jeśli już mamy cookie, nie rób dodatkowego requestu.
  if (getCookieValue("csrftoken")) return;

  if (csrfInitPromise) return csrfInitPromise;

  const url = new URL("/_allauth/browser/v1/auth/session", CONFIG.BASE_URL);

  csrfInitPromise = fetch(url.toString(), {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "x-api-version": CONFIG.VERSION,
    },
  })
    .then(() => undefined)
    .finally(() => {
      csrfInitPromise = null;
    });

  return csrfInitPromise;
}

export function setupAuthInterceptor(apiClient: AxiosInstance): {
  request: number;
  response: number;
} {
  // ─── Request ───────────────────────────────────────────────────────────────
  const request = apiClient.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
      // Zawsze wysyłaj cookies/credentials (wymagane przez Django session + CSRF)
      config.withCredentials = true;

      // Web (browser): do metod modyfikujących dołącz CSRF z cookie.
      // SessionAuthentication w DRF wymaga CSRF na POST/PUT/PATCH/DELETE.
      if (!isNative && isUnsafeMethod(config.method)) {
        await ensureWebCsrfCookie();
        const csrfToken = getCookieValue("csrftoken");
        if (csrfToken) {
          // Axios w runtime normalizuje nagłówki; trzymamy się Django default.
          (config.headers as any)["X-CSRFToken"] ??= csrfToken;
        }
      }

      if (isNative) {
        const sessionToken = await authStorage.getSessionToken();
        if (sessionToken) {
          config.headers["X-Session-Token"] = sessionToken;
        }
      }

      return config;
    },
    (error) => Promise.reject(error),
  );

  // ─── Response ──────────────────────────────────────────────────────────────
  const response = apiClient.interceptors.response.use(
    async (res) => {
      if (isNative) {
        // Odśwież session token jeśli pojawił się w odpowiedzi allauth
        const token = res.data?.meta?.session_token;
        if (typeof token === "string") {
          await authStorage.setSessionToken(token);
        }
      }
      return res;
    },
    async (error) => {
      const status = error.response?.status;

      if (isNative) {
        if (status === 401 || status === 410) {
          // Wyczyść token — auth.service/hooks obsłużą nawigację
          await authStorage.removeSessionToken();
        }
      }

      return Promise.reject(error);
    },
  );

  return { request, response };
}
