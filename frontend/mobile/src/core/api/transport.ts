import { configureApi } from "@olivin/api";
import type { HttpMethod, HttpRequestConfig } from "@olivin/api";
import { httpClient } from "@core/http/client";
import { handleAllauthSessionLifecycle } from "@core/auth/session-lifecycle";

/**
 * Implementacja transportu dla aplikacji mobilnej.
 *
 * Pakiet @olivin/api zna endpointy, ale nie wie, czym wykonać żądanie — bo to
 * różni się między celami. Tutaj podłączamy klienta HTTP tej aplikacji: nagłówek
 * z tokenem sesji z bezpiecznego magazynu urządzenia i obsługę cyklu życia sesji
 * allauth. Wersja webowa dostarczy własną, opartą na ciasteczkach.
 */

const HTTP_METHODS = new Set<HttpMethod>([
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "HEAD",
  "OPTIONS",
]);

function toHttpMethod(method?: string): HttpMethod | undefined {
  if (!method) return undefined;
  const normalized = method.toUpperCase() as HttpMethod;
  return HTTP_METHODS.has(normalized) ? normalized : undefined;
}

function toConfig(url: string, options: RequestInit): HttpRequestConfig {
  return {
    url,
    method: toHttpMethod(options.method),
    headers: options.headers,
    body: options.body,
    signal: options.signal ?? undefined,
  };
}

/**
 * Podłącza transport. Wywoływane raz, w layoucie głównym, zanim którykolwiek
 * ekran wykona żądanie.
 */
export function configureMobileApi(): void {
  configureApi({
    app: async <TData>(url: string, options: RequestInit = {}) => {
      return httpClient.request(toConfig(url, options)) as Promise<TData>;
    },

    // Allauth ma własny cykl życia sesji: odpowiedź może zawierać nowy token
    // sesji, który trzeba zapisać, a statusy 401 i 410 są tu normalną częścią
    // protokołu, nie błędem — stąd acceptStatuses "all".
    auth: async <TData>(url: string, options: RequestInit = {}) => {
      const response = await httpClient.request({
        ...toConfig(url, options),
        acceptStatuses: "all",
      });

      await handleAllauthSessionLifecycle(response);

      return response as TData;
    },
  });
}
